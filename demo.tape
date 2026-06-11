# VHS tape — generates demo.gif for the README.
# Install VHS: https://github.com/charmbracelet/vhs
# Run: vhs demo.tape

Output demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1100
Set Height 700
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 35ms

Type "cd /Users/prasannakumar/Documents/Claude/Projects/mcp-sploit && source .venv/bin/activate && clear"
Enter
Sleep 500ms

Type "mcp-sploit"
Enter
Sleep 2s

Type "use auxiliary/scanner/mcp_enum"
Enter
Sleep 500ms
Type "set TARGET http://localhost:8765"
Enter
Sleep 500ms
Type "run"
Enter
Sleep 2500ms

Type "use exploit/mcp/file_exfiltration"
Enter
Sleep 500ms
Type "set TARGET http://localhost:8765"
Enter
Sleep 500ms
Type "set FILE /etc/hostname"
Enter
Sleep 500ms
Type "check"
Enter
Sleep 1500ms
Type "exploit"
Enter
Sleep 2500ms

Type "use exploit/mcp/prompt_injection"
Enter
Sleep 500ms
Type "set TARGET http://localhost:8765"
Enter
Sleep 500ms
Type "exploit"
Enter
Sleep 3s

Type "exit"
Enter
Sleep 1s
