import glob
import os

total_code_lines = 0
total_blank_lines = 0
total_comment_lines = 0
total_functions = 0
total_async_functions = 0
total_classes = 0
file_count = 0
path = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), "AdditionalPylons")))  # "name" for project folder name
include = ["additionalpylons.py", "adept.py", "archive.py", "archon.py", "builder.py", "building_list.py", "carrier.py", "colossus.py", "cybercore.py", "disruptor.py", "disruptor_phased.py", "fleet.py", "forge.py", "gateway.py", "hightemplar.py", "immortal.py", "mothership.py", "nexus.py", "observer.py", "phoenix.py", "probe.py", "protoss_agent.py", "robo.py", "robobay.py", "sentry.py", "shade.py", "stalker.py", "stargate.py", "strategist.py", "tempest.py", "trainer.py", "trainingdata.py", "twilight.py", "unit_counters.py", "unit_list.py", "voidray.py", "zealot.py"]  # "name" for filename, "\\name\\" for folders
for filename in glob.glob(f"{path}/**/*.py", recursive=True):
    if any([string in filename for string in include]):
        file_count += 1
        with open(filename) as file:
            for line in file:
                # Count code occurences
                if "async " in line:
                    total_async_functions += 1
                elif "def " in line:
                    total_functions += 1
                elif "class " in line:
                    total_classes += 1

                # Count kind of line
                if "#" in line or '"""' in line:
                    total_comment_lines += 1
                elif line.strip():
                    total_code_lines += 1
                else:
                    total_blank_lines += 1

all_lines = total_code_lines + total_blank_lines + total_comment_lines

print(f"{'Files:':<16}{file_count:>5}")
print(f"{'Lines:':<16}{all_lines:>5}")
print(f"{'Code Lines:':<16}{total_code_lines:>5} ({round(total_code_lines*100 / all_lines):>2}%)")
print(f"{'Comments:':<16}{total_comment_lines:>5} ({round(total_comment_lines*100 / all_lines):>2}%)")
print(f"{'Blank Lines:':<16}{total_blank_lines:>5} ({round(total_blank_lines*100 / all_lines):>2}%)")
print(f"{'Classes:':<16}{total_classes:>5}")
print(f"{'Functions:':<16}{total_functions:>5}")
print(f"{'Async Functions:':<16}{total_async_functions:>5}")