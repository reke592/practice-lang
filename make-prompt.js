const mcp_code = "dev"
const interrupt_id = ""
const message = `
there is a bug, when rendering the final message it shows Connection closed or stream ended unexpectedly.
`.trim()

console.log(JSON.stringify({
  message,
  mcp_code,
  interrupt_id
}))