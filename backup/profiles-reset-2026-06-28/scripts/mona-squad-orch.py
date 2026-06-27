import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "mona-workspace" / "mona-squad"))
sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))

from squad import send_message, read_inbox, check_all_inboxes, AGENTS

# Import orchestrator logic
import importlib.util
spec = importlib.util.spec_from_file_location("orch", str(Path.home() / "mona-workspace" / "mona-squad" / "orchestrator.py"))
orch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orch)
result = orch.run_orchestrator()
# Silent — cron runs quietly
