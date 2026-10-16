from mcp.server.fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP("ResumeScreeningAgent")


@mcp.tool()
def screen_candidate(resume_text: str, job_description: str) -> str:
    """
    Analyzes a resume against a JD and returns a match score and summary.
    This is the code you already built/pushed to GitHub.
    """
    # YOUR EXISTING LOGIC HERE
    # result = my_screening_logic(resume_text, job_description)
    return f"Match Score: 85%. Key Skills Found: Python, Webex API."


if __name__ == "__main__":
    mcp.run()
