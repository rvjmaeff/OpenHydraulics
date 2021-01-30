"""
This script bulk runs all the *.mos files in this directory.
Currently, the criteria for passing a test is a successful compiling and simulation.
"""

from OMPython import OMCSessionZMQ
import os
import shutil
import argparse
import tempfile
from datetime import datetime
import re


def check_pass(string: str) -> bool:
    """checks string against pass/fail criteria"""

    if "The simulation finished successfully." in string:
        return True
    if "Simulation Failed" in string:
        return False
    if "Simulation execution failed" in string:
        return False
    if "0.0" in string:
        return False
    if "LOG_FAILURE" in string:
        return False
    if " Failed" in string:
        return False
    
    return False


def simulation_record_to_dict(record: str) -> dict:
    """converts string output of omc record string to python dict"""

    # order matters
    keys = [
        "resultsFile",
        "messages",
        "simulationOptions",
        "timeFrontend",
        "timeBackend",
        "timeSimCode",
        "timeTemplates",
        "timeCompile",
        "timeSimulation",
        "timeTotal",
        "end SimulationResult"
    ]

    regexPattern = '|'.join(map(re.escape, [k + " = " for k in keys]))
    record = re.split(regexPattern, record)[1:-2]

    results = {}
    for k, v in zip(keys, record):
        results[k] = v.replace(",", "").replace("\n", "").strip()

    return results

def parser():
    parser = argparse.ArgumentParser(
        description="Run .mos scripts for testing simulations, and report results."
    )
    parser.add_argument(
        "package",
        type=str,
        help="location of root package.mo of library to simulate",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="*.mos file or directory containing *.mos scripts",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="output directory for results (using cd() in omc). By default results stored in temp folder that is automatically deleted after running.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Print results of each script output and error strings.",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--log",
        type=str,
        help="optional directory to output a log.txt file of script results and error string.",
    )
    return parser


if __name__ == "__main__":
    parser = parser()
    args = parser.parse_args()

    if args.input:
        INPUT = os.path.abspath(args.input)
    else:
        INPUT = os.getcwd()

    if args.output:
        if os.path.isdir(args.output):
            OUTPUT = os.path.abspath(args.output)
        else:
            sys.exit("Location specified for output is not a directory")
    else:
        temp_dir = tempfile.TemporaryDirectory()
        OUTPUT = temp_dir.name

    if args.log:
        if os.path.isdir(args.log):
            LOG_PATH = os.path.abspath(args.log)
        else:
            sys.exit("Location specified for log is not a directory")

    log = []
    failed = []

    omc = OMCSessionZMQ()
    omc.sendExpression(f'loadFile("{args.package}");')
    omc.sendExpression(f'cd("{OUTPUT}")')

    if os.path.isdir(INPUT):
        filepaths = [INPUT + "/" +f for f in os.listdir(INPUT) if f.endswith(".mos")]
        if len(filepaths) == 0:
            sys.exit("No *.mos files in directory")
    else:
        if os.path.basename(INPUT).endswith(".mos"):
            filepaths = os.path.basename(INPUT)
        else:
            sys.exit("File is not a *.mos script")

    nfiles = len(filepaths)
    fn = 1
    print(f"Collected {nfiles} *.mos scripts.")
    for fname in filepaths:
        name = os.path.basename(fname)
        print(f"Running script {fn} of {nfiles}: {name}...", end="")

        if args.output:
            # Go to sub directory for results
            result_dir = OUTPUT + "/" + name.replace(".mos", "")

            try:
                os.mkdir(result_dir)
            except OSError as e:
                print(f"Failed to create results directory {result_dir}")
                sys.exit(1)

            omc.sendExpression(f'cd("{result_dir}")')

        res = omc.sendExpression(f'runScript("{fname}")')
        errors = omc.sendExpression("getErrorString()").split("\n")

        if args.output:
            # Return to parent results
            omc.sendExpression(f'cd("{OUTPUT}")')

        results = simulation_record_to_dict(res)

        check_strings = [
            results.get("messages"),
        ]
        check_strings.extend(errors)

        success = map(check_pass, check_strings)

        # logging
        log.append(name)
        log.append(fname)
        log.append(res)
        log.extend(errors)
        log.append("#" * 72)

        if any(success):
            print(" Passed")

        # Otherwise passed
        else:
            print(" Failed")
            failed.append(name)
            # Verbose printing
            if args.verbose:
                for b, m in zip(success, check_strings):
                    if not b:
                        print(m)
            

        fn += 1

    print("Failed Simulations:")
    for f in failed:
        print("\t"+f)

    if not args.output:
        temp_dir.cleanup()

    if args.log:
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        with open(LOG_PATH + "/." + now + "-log.txt", 'w') as f:
            f.write("\n".join(log))
                
