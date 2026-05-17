import sys
sys.stdout.reconfigure(encoding='utf-8')
import io, contextlib
from graphplan import DoPlan

# Redirect stdout to capture
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    plan = DoPlan('Exemples/r_ops.txt', 'Exemples/r_fact9.txt')

output = buf.getvalue()
lines = output.splitlines()
# Print last 35 lines
for l in lines[-35:]:
    print(l)
print(f"\nTotal output lines: {len(lines)}")
