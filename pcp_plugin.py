#!/usr/bin/env python3.9

import json
import subprocess
import sys
import typing
from arcaflow_plugin_sdk import plugin
from pcp_schema import (
    InputParams,
    PerfOutput,
    Error,
)


@plugin.step(
    id="start-pcp",
    name="Start PCP",
    description="Start the PCP data logging tools",
    outputs={"success": PerfOutput, "error": Error},
)
def start_pcp(
    params: InputParams,
) -> typing.Tuple[str, typing.Union[PerfOutput, Error]]:

    pcmd_cmd = [
        "/usr/libexec/pcp/lib/pmcd",
        "start",
    ]

    # Start the PCMD daemon
    print("==>> Starting PCMD ...")
    try:
        print(
            subprocess.check_output(
                pcmd_cmd,
                text=True,
                stderr=subprocess.STDOUT,
            )
        )
    except subprocess.CalledProcessError as error:
        return "error", Error(
            "{} failed with return code {}:\n{}".format(
                error.cmd[0], error.returncode, error.output
            )
        )

    sar_cmd = [
        "/usr/lib64/sa/sa1",
        "1",
    ]

    # Start SAR collection
    print("==>> Starting SAR ...")
    try:
        print(
            subprocess.Popen(
                sar_cmd,
                text=True,
                stderr=subprocess.STDOUT,
            )
        )
    except subprocess.CalledProcessError as error:
        return "error", Error(
            "{} failed with return code {}:\n{}".format(
                error.cmd[0], error.returncode, error.output
            )
        )

    pmlogger_cmd = [
        "pmlogger",
        "-c",
        "pmlogger.conf",
        "-t",
        "1",
        "pmlogger-out",
    ]

    # Start pmlogger
    print("==>> Starting pmlogger ...")
    try:
        print(
            subprocess.run(
                pmlogger_cmd,
                text=True,
                stderr=subprocess.STDOUT,
                timeout=params.run_duration,
            )
        )
        # It should not end itself, so getting here means there was an
        # error.
        return "error", Error(
            result.returncode,
            result.stdout.decode("utf-8") + result.stderr.decode("utf-8"),
        )
    except subprocess.CalledProcessError as error:
        return "error", Error(
            "{} failed with return code {}:\n{}".format(
                error.cmd[0], error.returncode, error.output
            )
        )
    except subprocess.TimeoutExpired:
        # Worked as intended. It doesn't end itself, so it finished when it
        # timed out.
        #pcp2json -a _pcp/${PTS_FILENAME} -t 1s -c pts/pcp2json.conf :sar :sar-b :sar-r :collectl-sn -E | tail -n+3 > ${PTS_FILENAME}.json
        pcp2json_cmd = [
            "pcp2json",
            "-a",
            "pmlogger-out",
            "-t",
            "1s",
            "-c",
            "pcp2json.conf",
            ":sar",
            ":sar-b",
            ":sar-r",
            "-E",
        ]
        # Start the PCMD daemon
        print("==>> Converting output to json...")
        try:
            pcp_out = (
                subprocess.check_output(
                    pcp2json_cmd,
                    text=True,
                    stderr=subprocess.STDOUT,
                )
            ).strip().split("\n",2)[2]
            pcp_out_json = json.loads(pcp_out)
        except subprocess.CalledProcessError as error:
            return "error", Error(
                "{} failed with return code {}:\n{}".format(
                    error.cmd[0], error.returncode, error.output
                )
            )
        return "success", PerfOutput(pcp_out_json)



if __name__ == "__main__":
    sys.exit(
        plugin.run(
            plugin.build_schema(
                # List your step functions here:
                start_pcp,
            )
        )
    )
