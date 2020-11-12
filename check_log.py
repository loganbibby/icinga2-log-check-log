import argparse
import copy
import os
import os.path
import json
import re
import sys

log_flags_template = {
	"last_size": 0,
}	

def build_parser():
	parser = argparse.ArgumentParser(description="Check log file and report back to Icinga2")
	parser.add_argument("--file", dest="log_filename", action="store", help="Log filename (absolute path)")
	parser.add_argument("--regex", dest="regex_pattern", action="store", help="Regular expression pattern")
	parser.add_argument("--negate", dest="negate", action="store_true", help="Only critical when not found")
	parser.add_argument("--flags-file", dest="flags_filename", action="store", help="Flags filename", default="check_log_flags.json")
	parser.add_argument("--debug", dest="debug", action="store_true")
	return parser.parse_args()

def main():
	args = build_parser()
	
	def write_log(msg, severity="info"):
		if args.debug:
			print("{}: {}".format(severity, msg))
		pass
	
	# Read in flags
	if not os.path.isfile(args.flags_filename):
		# Create a new flags file
		flags = {
			args.log_filename: copy.deepcopy(log_flags_template)
		}
		with open(args.flags_filename, "w") as fh:
			json.dump(flags, fh)
			write_log("Flags file missing so a new one was created: {}".format(args.flags_filename), "debug")

	with open(args.flags_filename, "r") as fh:
		flags = json.load(fh)
		write_log("Read flags from file: {}".format(args.flags_filename), "debug")
		write_log("{}".format(flags), "debug")

	if args.log_filename not in flags:
		flags[args.log_filename] = copy.deepcopy(log_flags_template)
		

	# Check log file size
	if not os.path.isfile(args.log_filename):
		# TODO: needs error handling
		pass

	log_size = os.path.getsize(args.log_filename)
	buffer = log_size
	seek = flags[args.log_filename]["last_size"]
	tell = 0

	if buffer > flags[args.log_filename]["last_size"]:
		buffer = buffer - flags[args.log_filename]["last_size"]
	elif buffer < flags[args.log_filename]["last_size"]:
		seek = 0

	with open(args.log_filename, "r") as fh:
		fh.seek(seek)
		lines = fh.readlines()
		tell = fh.tell()

	match = None
	log_pattern = re.compile(args.regex_pattern)

	for line in lines:
		if line == "\n":
			continue
		
		match = log_pattern.search(line)
		
		if match:
			break

	# Save updated flags
	flags[args.log_filename]["last_size"] = tell

	with open(args.flags_filename, "w") as fh:
		json.dump(flags, fh)

	# Handle output
	if match and not args.negate:
		# There was a match, let's go critical
		print("{} | 'pattern_found'=1;1;1;0;1".format(match.string))
		sys.exit(2)
	elif not match and args.negate:
		# There was not a match and there should be, let's go critcal
		print("No match found | 'pattern_found'=0;0;0;0;1")
		sys.exit(2)
	else:
		# All is well
		print("All's well | 'pattern_found'={};{};{};0;1".format(
			"1" if args.negate else "0",
			"0" if args.negate else "1",
			"0" if args.negate else "1"
		))
		sys.exit(0)
		
if __name__ == '__main__':
	main()
	sys.exit(0)