import os
from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markup import escape
from .agent import CerebrasAgent
import tempfile
import difflib
import shutil
import subprocess
from pathlib import Path
import re

app = typer.Typer(add_completion=False)
console = Console()

# Global debug flag
DEBUG_MODE = False

# Create a temporary directory for storing diffs
DIFFS_DIR = Path(tempfile.gettempdir()) / "cerebras_agent_diffs"
DIFFS_DIR.mkdir(exist_ok=True)

def clear_old_diffs():
    """Clear old diff files from the temporary directory."""
    for file in DIFFS_DIR.glob("*.diff"):
        try:
            file.unlink()
        except Exception:
            pass

def create_diff_link(file_path: str, original_content: str, new_content: str) -> str:
    """Create a diff file and return a clickable link."""
    # Create a unique filename for this diff
    diff_file = DIFFS_DIR / f"{Path(file_path).name}_{os.urandom(4).hex()}.diff"
    
    # Generate the diff
    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}"
    )
    
    # Write the diff to file
    with open(diff_file, 'w') as f:
        f.writelines(diff)
    
    # Return a clickable link
    return f"file://{diff_file.absolute()}"

def display_welcome():
    """Display a welcome message with the agent's logo."""
    coder_ascii = """
   ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
  ██║     ██║   ██║██║  ██║█████╗  ██████╔╝
  ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗
  ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                           
   Cerebras Agent - Your AI coding assistant
    """
    console.print(coder_ascii, style="bold blue")
    console.print(Panel.fit(
        "[italic]Powered by Cerebras AI[/italic]",
        border_style="blue"
    ))

def display_help():
    """Display the help message with available commands."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    
    commands = [
        ("<prompt>", "Chat-like interaction that will end with an Accept/Reject alternative (include checkpoint number)"),
        ("ask <question>", "Chat-like prompt that is not generating any changes on the files"),
        ("help", "Show this help message"),
        ("checkpoint", "Show current checkpoint and change history"),
        ("revert <number>", "Revert to checkpoint number"),
        ("exit", "Exit the program")
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    
    console.print(Panel(table, title="📚 Available Commands", border_style="blue"))

def process_suggested_changes(agent_instance, suggested_changes, context):
    """Process suggested changes from the agent."""
    if not suggested_changes:
        console.print("[red]❌ No changes were suggested[/red]")
        return

    # Extract file changes and shell commands
    file_steps = []
    shell_commands = []
    
    for step in suggested_changes.get('steps', []):
        if step.get('tool') == 'file_ops':
            file_steps.append(step)
        elif step.get('tool') == 'shell':
            shell_commands.append(step.get('command'))
    
    # Display file changes first
    if file_steps:
        console.print("\n[bold blue]📝 Suggested File Changes:[/bold blue]")
        for i, step in enumerate(file_steps):
            if step.get('action') == 'write':
                file_path = step.get('target')
                new_code = step.get('content', '')
                
                # Get original content for diff
                try:
                    with open(os.path.join(agent_instance.repo_path, file_path), 'r') as f:
                        original_content = f.read()
                except Exception:
                    original_content = ""
                diff_link = create_diff_link(file_path, original_content, new_code)
                
                # Display each file with a numbered header and distinctive styling
                console.print(f"\n[bold cyan]FILE {i+1} OF {len(file_steps)}:[/bold cyan]")
                console.print(f"[bold yellow]📄 {file_path}[/bold yellow] [link={diff_link}]View diff[/link]")
                console.print(Panel(new_code, border_style="green", title=f"Content for {file_path}"))
    else:
        console.print("[yellow]No file changes suggested[/yellow]")
    
    # First ask to apply file changes
    files_created = False
    if file_steps:
        if Confirm.ask("\n[bold green]Would you like to create/update these files?[/bold green]"):
            for step in file_steps:
                if step["tool"] == "file_ops" and step["action"] == "write":
                    # Create the directories and files by executing the step
                    file_path = step["target"]
                    # Remove any backticks from filenames that might have been parsed from markdown
                    if file_path.startswith('`') and file_path.endswith('`'):
                        file_path = file_path[1:-1]  # Remove backticks
                        step["target"] = file_path  # Update the target in the step
                    
                    # Remove quotes if present
                    if file_path.startswith('"') and file_path.endswith('"'):
                        file_path = file_path[1:-1]  # Remove double quotes
                        step["target"] = file_path
                    if file_path.startswith("'") and file_path.endswith("'"):
                        file_path = file_path[1:-1]  # Remove single quotes
                        step["target"] = file_path
                    
                    # Remove descriptive prefixes
                    prefixes_to_remove = ["New File:", "Existing Python File", "Existing File:", "New Python File:"]
                    for prefix in prefixes_to_remove:
                        if file_path.startswith(prefix):
                            file_path = file_path[len(prefix):].strip()
                            step["target"] = file_path
                            break
                    
                    # Make sure the file's directory exists
                    os.makedirs(os.path.dirname(os.path.join(agent_instance.repo_path, file_path)), exist_ok=True)
                    # Execute the step to create or modify the file
                    result = agent_instance._execute_plan_step(step)
                    if result:
                        files_created = True
                        console.print(f"[green]✅ Created/updated {file_path}[/green]")
                    else:
                        console.print(f"[red]❌ Failed to create/update {file_path}[/red]")
        else:
            console.print("[yellow]↩️ File changes were not applied[/yellow]")
    
    # Only show shell commands if there are any and the user explicitly requests them
    if shell_commands and any(cmd.strip() for cmd in shell_commands):
        if Confirm.ask("\n[bold green]Would you like to see the suggested shell commands?[/bold green]"):
            # Filter out non-command text from shell commands
            valid_shell_commands = []
            current_command = []
            for cmd in shell_commands:
                # Skip commands that are too long or contain too many spaces (likely explanations)
                if len(cmd) > 200 or cmd.count(' ') > 20 or cmd.count('`') > 2:
                    continue
                # Skip commands that start with common explanation text
                if any(cmd.lower().startswith(prefix) for prefix in ['this ', 'the ', 'these ', 'note ', 'now ', 'make sure ', 'ensure ', 'remember ', 'important: ', 'note: ']):
                    continue
                # Skip commands that are just notes or explanations
                if cmd.lower().startswith('note:') or 'make sure' in cmd.lower() or 'replace' in cmd.lower():
                    continue
                
                # Check if this is a continuation of a previous command
                if cmd.strip().startswith('echo') and "'" in cmd:
                    # This is likely a multiline echo command
                    current_command.append(cmd)
                elif cmd.strip().startswith('echo') and '"' in cmd:
                    # This is likely a multiline echo command
                    current_command.append(cmd)
                elif current_command:
                    # If we have a current command and this line looks like a continuation
                    if not cmd.strip().startswith(('mkdir', 'cd', 'cargo', 'npm', 'pip', 'python', 'node')):
                        current_command.append(cmd)
                    else:
                        # Join and add the previous command
                        valid_shell_commands.append('\n'.join(current_command))
                        current_command = [cmd]
                else:
                    current_command = [cmd]
            
            # Add any remaining command
            if current_command:
                valid_shell_commands.append('\n'.join(current_command))
            
            shell_commands = valid_shell_commands
            
            # Display shell commands
            console.print("\n[bold blue]====================================[/bold blue]")
            console.print("[bold blue]🔧 SHELL COMMANDS[/bold blue]")
            console.print("[bold blue]====================================[/bold blue]")
            
            # Remove duplicate commands before displaying
            unique_commands = []
            for cmd in shell_commands:
                if cmd not in unique_commands:
                    unique_commands.append(cmd)
            
            shell_commands = unique_commands  # Replace with deduplicated list
            
            for i, cmd in enumerate(shell_commands):
                # Split multiline commands for display
                cmd_lines = cmd.split('\n')
                if len(cmd_lines) > 1:
                    console.print(f"[cyan]Command {i+1}:[/cyan]")
                    for j, line in enumerate(cmd_lines):
                        if j == 0:
                            console.print(f"[bold white]{line}[/bold white]")
                        else:
                            console.print(f"      {line}")
                else:
                    console.print(f"[cyan]Command {i+1}:[/cyan] [bold white]{cmd}[/bold white]")
            
            # Only ask to execute commands if files were created successfully
            if not file_steps or files_created:
                if Confirm.ask("\n[bold green]Would you like to execute these shell commands?[/bold green]"):
                    # Change to the repository directory before executing commands
                    repo_path = str(agent_instance.repo_path)
                    
                    # Modify commands to run in the repository directory
                    modified_commands = []
                    for cmd in shell_commands:
                        # Handle virtual environment activation specially
                        if cmd.strip().startswith('source ') and ('venv/bin/activate' in cmd or 'venv/Scripts/activate' in cmd):
                            # For virtual environment activation, we'll use subprocess directly
                            if Confirm.ask(f"\n[bold yellow]Execute command: {cmd}?[/bold yellow]"):
                                console.print(f"[yellow]Executing in {repo_path}: {cmd}[/yellow]")
                                try:
                                    # Use subprocess.run directly for venv activation
                                    result = subprocess.run(
                                        cmd,
                                        shell=True,
                                        cwd=repo_path,
                                        capture_output=True,
                                        text=True
                                    )
                                    if result.returncode == 0:
                                        console.print("[green]✅ Command executed successfully![/green]")
                                    else:
                                        console.print(f"[red]❌ Command failed with exit code {result.returncode}[/red]")
                                        if result.stderr:
                                            console.print(f"[red]Error: {result.stderr}[/red]")
                                except Exception as e:
                                    console.print(f"[red]❌ Failed to execute command: {str(e)}[/red]")
                            continue
                        
                        # Skip cd commands as we'll handle directory change ourselves
                        if cmd.strip().startswith("cd "):
                            continue
                        modified_commands.append(cmd)
                    
                    # Execute each command individually with confirmation
                    for cmd in modified_commands:
                        if Confirm.ask(f"\n[bold yellow]Execute command: {cmd}?[/bold yellow]"):
                            console.print(f"[yellow]Executing in {repo_path}: {cmd}[/yellow]")
                            try:
                                # Create a step with execute=True to indicate explicit execution
                                step = {
                                    "tool": "shell",
                                    "action": "run",
                                    "command": cmd,
                                    "execute": True
                                }
                                
                                result = agent_instance._execute_plan_step(step)
                                
                                if result and isinstance(result, dict) and result.get('error'):
                                    error_output = result['error']
                                    console.print(f"[red]❌ Command failed: {error_output}[/red]")
                                elif result:
                                    console.print("[green]✅ Command executed successfully![/green]")
                                else:
                                    console.print("[red]❌ Command failed[/red]")
                            except Exception as e:
                                console.print(f"[red]❌ Failed to execute command: {str(e)}[/red]")
                        else:
                            console.print(f"[yellow]↩️ Skipped command: {cmd}[/yellow]")
                    
                    console.print("[green]✅ Process completed![/green]")
                else:
                    console.print("[yellow]↩️ Commands were not executed[/yellow]")
            elif file_steps and not files_created:
                console.print("[yellow]⚠️ Cannot run commands as file creation was skipped. Please create the necessary files first.[/yellow]")

@app.command()
def main(
    ask: Optional[str] = typer.Option(
        None,
        "--ask",
        "-a",
        help="Ask a question about the repository without making changes"
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-g",
        help="Prompt the agent to perform changes in the repository"
    ),
    repo: Optional[str] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Path to the repository to analyze (default: current directory)"
    ),
    model: Optional[str] = typer.Option(
        "qwen-3-32b",
        "--model",
        help="Model to use (default: qwen-3-32b)"
    ),
    no_think: bool = typer.Option(
        False,
        "--no-think",
        help="Disable Qwen-3-32b thinking mode by appending /no_think to the prompt"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug output"
    )
):
    """Cerebras Agent - A local agent for code development using Cerebras API."""
    global DEBUG_MODE
    DEBUG_MODE = debug
    
    try:
        # Clear old diffs at startup
        clear_old_diffs()
        
        # Use the provided repo path or default to current directory
        repo_path = repo if repo else "."
        
        # Initialize agent with the specified repository path and model
        agent_instance = CerebrasAgent(repo_path=repo_path, model=model)
        
        # Analyze repository
        console.print(f"[green]🔍 Analyzing repository: {repo_path}[/green]")
        context = agent_instance.analyze_repository(repo_path)
        
        if ask:
            # Optionally append /no_think for Qwen-3-32b
            question = ask
            if model.startswith("qwen-3") and no_think:
                question = f"{ask} /no_think"
            answer = agent_instance.ask_question(question, context)
            agent_instance.display_response(answer)
        elif agent:
            # Optionally append /no_think for Qwen-3-32b
            prompt = agent
            if model.startswith("qwen-3") and no_think:
                prompt = f"{agent} /no_think"
            console.print("[yellow]🤔 Analyzing repository and preparing changes...[/yellow]")
            suggested_changes = agent_instance.prompt_complex_change(prompt)
            process_suggested_changes(agent_instance, suggested_changes, context)
        else:
            # No command-line options provided, start interactive mode
            display_welcome()
            console.print("[yellow]💡 Type 'help' to see available commands[/yellow]")
            
            while True:
                user_input = Prompt.ask("\n[bold green]What would you like to do?[/bold green]")
                
                if user_input.lower() == 'exit':
                    if Confirm.ask("Are you sure you want to exit?"):
                        # Clear diffs before exiting
                        clear_old_diffs()
                        console.print("[yellow]👋 Goodbye![/yellow]")
                        break
                elif user_input.lower() == 'help':
                    display_help()
                elif user_input.lower() == 'checkpoint':
                    console.print(f"\n[blue]📌 Current checkpoint: {agent_instance._current_checkpoint}[/blue]")
                    if agent_instance._change_history:
                        console.print("\n[bold blue]📝 Change History:[/bold blue]")
                        for i, (file_path, original_code, new_code) in enumerate(agent_instance._change_history):
                            diff_link = create_diff_link(file_path, original_code, new_code)
                            console.print(f"[cyan]{i}: {file_path}[/cyan] [link={diff_link}]View diff[/link]")
                    else:
                        console.print("[yellow]No changes in history[/yellow]")
                elif user_input.lower().startswith('ask '):
                    question = user_input[4:].strip()
                    if model.startswith("qwen-3") and no_think:
                        question = f"{question} /no_think"
                    answer = agent_instance.ask_question(question, context)
                    agent_instance.display_response(answer)
                elif user_input.lower().startswith('revert '):
                    try:
                        checkpoint = int(user_input[7:].strip())
                        if agent_instance.revert_to_checkpoint(checkpoint):
                            console.print(f"[green]✅ Successfully reverted to checkpoint {checkpoint}[/green]")
                        else:
                            console.print(f"[red]❌ Failed to revert to checkpoint {checkpoint}[/red]")
                    except ValueError:
                        console.print("[red]❌ Error: Invalid checkpoint number[/red]")
                else:
                    # Treat any other input as a prompt command
                    if not user_input.strip():
                        console.print("[yellow]❓ Please enter a command or description[/yellow]")
                        continue
                    prompt = user_input
                    if model.startswith("qwen-3") and no_think:
                        prompt = f"{user_input} /no_think"
                    console.print("[yellow]🤔 Analyzing repository and preparing changes...[/yellow]")
                    suggested_changes = agent_instance.prompt_complex_change(prompt)
                    process_suggested_changes(agent_instance, suggested_changes, context)
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)
    finally:
        # Clear diffs on exit
        clear_old_diffs()

def display_changes(changes: dict):
    """Display suggested changes in a formatted way."""
    if not changes or not changes.get("steps"):
        print("❌ No changes were suggested")
        return

    print("\n📝 Suggested Changes:")
    for step in changes["steps"]:
        if step["tool"] == "file_ops" and step["action"] == "write":
            print(f"\n📄 {step['target']}:")
            content = step["content"]
            if isinstance(content, str):
                lines = content.splitlines()
                for line in lines:
                    print(f"  {line}")
            else:
                print(f"  {content}")

if __name__ == "__main__":
    app() 