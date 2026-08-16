from typing import Any, Dict

from pydantic import BaseModel


class MCPSkill(BaseModel):
  name: str
  description: str
  uri: str


def generate_llm_schema(model: type[BaseModel], escape_chars: bool = True, additional_constraints: list[str] = []) -> str:
    """Converts a Pydantic model into a clean text format optimized for LLMs, 
    supporting deeply nested models and definitions.
    """

    schema = model.model_json_schema()
    # Pydantic v2 stores shared nested models in '$defs'
    defs = schema.get("$defs", {})

    def resolve_ref(prop: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to resolve JSON schema $ref pointers to actual definitions."""
        if "$ref" in prop:
            ref_name = prop["$ref"].split("/")[-1]
            return defs.get(ref_name, prop)
        return prop

    def parse_property_type(prop: Dict[str, Any]) -> str:
        """Recursively parses a property dictionary into a string representation."""
        prop = resolve_ref(prop)
        
        if "anyOf" in prop:
            types = []
            for sub_prop in prop["anyOf"]:
                sub_prop = resolve_ref(sub_prop)
                if "type" in sub_prop:
                    types.append(parse_property_type(sub_prop))
                elif "$ref" in sub_prop:
                    types.append(parse_property_type(sub_prop))
            return " | ".join(filter(None, types)) or "any"
        
        field_type = prop.get("type", "any")

        # Handle Deeply Nested Object
        if field_type == "object" and "properties" in prop:
            nested_lines = ["{"]
            for f_name, f_props in prop["properties"].items():
                f_props = resolve_ref(f_props)
                f_type = parse_property_type(f_props)
                f_desc = f_props.get("description", "")
                desc_suffix = f"  // {f_desc}" if f_desc else ""
                nested_lines.append(f'  "{f_name}": {f_type},{desc_suffix}')
            nested_lines.append("}")
            return "\n".join(nested_lines)

        # Handle Array of primitives or nested objects
        elif field_type == "array":
            items_prop = resolve_ref(prop.get("items", {}))
            items_type = parse_property_type(items_prop)
            
            # Formatting block arrays nicely if they are nested objects
            if "\n" in items_type:
                # Indent nested object arrays gracefully
                indented_items = items_type.replace("\n", "\n  ")
                return f"Array<\n  {indented_items}\n>"
            return f"Array<{items_type}>"

        return field_type

    # Start parsing the top-level schema
    lines = ["{"]
    for field_name, properties in schema.get("properties", {}).items():
        properties = resolve_ref(properties)
        field_type = parse_property_type(properties)
        description = properties.get("description", "")
        
        desc_suffix = f"  // {description}" if description else ""
        
        # If the returned type is a nested block, indent its inner contents nicely
        if "\n" in field_type:
            indented_type = field_type.replace("\n", "\n  ")
            lines.append(f'  "{field_name}": {indented_type},{desc_suffix}')
        else:
            lines.append(f'  "{field_name}": {field_type},{desc_suffix}')
            
    lines.append("}")
    
    final_output = "\n".join(lines)
    
    if escape_chars:
        # Escapes { to {{ and } to }} so it can safely be fed into .format() or f-strings
        final_output = final_output.replace('{', '{{').replace('}', '}}')

    # compute the constraints
    constraints = '\n'.join([ 
        f'- {item}' 
        for item in ["Do not use markdown formatting in your response. Respond only with the raw JSON format as specified."] + additional_constraints
    ])

    # the final output format for system prompt
    return (
       "# CONSTRAINTS\n"
       f"{constraints}\n\n"
       "# RESPONSE FORMAT\n"
       f"{final_output}"
    )