#!/usr/bin/env python3

from enum import Enum, StrEnum, auto
import subprocess
from multiprocessing import Pool
from itertools import repeat
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import shutil
import os
from numbers import Number
from collections import OrderedDict
import logging
import pandas as pd
import configparser


class FilesystemType(Enum):
    def __str__(self):
        return str(self.value)

    BTRFS = "btrfs"
    COPYFS = "copyfs"
    NILFS = "nilfs"
    NILFS_DEDUP = "nilfs-dedup"
    WAYBACKFS = "waybackfs"


class ToolName(Enum):
    def __str__(self):
        return str(self.value)

    BONNIE = "bonnie"
    FIO = "fio"
    DEDUP = "dedup"
    APPEND = "append"
    DELETE = "delete"


class FileExportType(Enum):
    def __str__(self):
        return str(self.value)

    SVG = "svg"
    JPG = "jpg"
    TEX = "tex"


FS_MOUNT_POINTS = {
    FilesystemType.BTRFS: "/dev/loop0",
    FilesystemType.COPYFS: "/dev/sda1",
    FilesystemType.NILFS: "/dev/loop0",
    FilesystemType.NILFS_DEDUP: "/dev/loop0",
    FilesystemType.WAYBACKFS: "/dev/sda1",
}

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = CURRENT_DIR + "/logs"
OUTPUT_DIR = CURRENT_DIR + "/output"
GRAPHS_OUTPUT_DIR = f"{OUTPUT_DIR}/graphs"
BONNIE_OUTPUT_DIR = f"{OUTPUT_DIR}/{ToolName.BONNIE}"

FIO_CONFIG = CURRENT_DIR + "/tests/fio-job.cfg"
BONNIE_CONFIG = CURRENT_DIR + "/tests/test_env.sh"


class PlotUnit(StrEnum):
    PERCENT = auto()
    SCALAR = auto()


class BarPlot:
    out_dir_jpg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.JPG}"
    out_dir_svg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.SVG}"

    def __init__(
        self,
        x: list[str],
        y: list[Number],
        xlabel: str,
        ylabel: str,
        title: str,
        filename: str,
        tool_name: ToolName,
        plot_unit: PlotUnit,
    ):
        self.x = x
        self.y = y
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.filename = filename
        self.plot_unit = plot_unit

        self.out_dir_jpg += f"/{tool_name}"
        self.out_dir_svg += f"/{tool_name}"
        create_dir(self.out_dir_jpg)
        create_dir(self.out_dir_svg)
        self.out_jpg = f"{self.out_dir_jpg}/{self.filename}.{FileExportType.JPG}"
        self.out_svg = f"{self.out_dir_svg}/{self.filename}.{FileExportType.SVG}"

        self.__plot()

    def __plot(self):
        logging.info(
            f"Generating {self.plot_unit} BarPlot: {self.out_jpg}, {self.out_svg}"
        )
        if self.plot_unit == PlotUnit.SCALAR:
            self.__plot_scalar()
        elif self.plot_unit == PlotUnit.PERCENT:
            self.__plot_percent()
        else:
            raise RuntimeError(f"Unrecognized plot unit: {self.plot_unit}")

    def __plot_scalar(self):
        plt.bar(np.arange(len(self.y)), self.y, color="blue", edgecolor="black")
        plt.xticks(np.arange(len(self.y)), self.x)
        plt.xlabel(self.xlabel, fontsize=16)
        plt.ylabel(self.ylabel, fontsize=16)
        plt.title(self.title, fontsize=16)
        plt.savefig(self.out_jpg, dpi=300)
        plt.savefig(self.out_svg)
        plt.cla()

    def __plot_percent(self):
        plt.bar(np.arange(len(self.y)), self.y, color="blue", edgecolor="black")
        plt.gca().set_yticklabels([f"{x:.0%}" for x in plt.gca().get_yticks()])
        plt.xticks(np.arange(len(self.y)), self.x)
        plt.xlabel(self.xlabel, fontsize=16)
        plt.ylabel(self.ylabel, fontsize=16)
        plt.title(self.title, fontsize=16)
        plt.savefig(self.out_jpg, dpi=300)
        plt.savefig(self.out_svg)
        plt.cla()


class TexTable:
    def __init__(
        self, df: pd.DataFrame, name: str, tool_name: ToolName, with_index: bool = True
    ):
        self.df = df
        self.name = name
        self.with_index = with_index
        self.output_dir = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.TEX}/{tool_name}"
        create_dir(self.output_dir)

    def export(self):
        filename = f"{self.output_dir}/{self.name}.{FileExportType.TEX}"
        logging.info(f"Exporting latex table to {filename}")
        self.df.to_latex(filename, index=self.with_index)


class SpaceUsageDf:
    class __DfResult:
        def __init__(self, before, after, name):
            self.before = before
            self.after = after
            self.name = name

        def x(self):
            return self.name

        def y(self):
            return (self.after - self.before) / 1000_000  # in gigabytes

    def __init__(
        self,
        input_file_before,
        input_file_after,
        output_image,
        title,
        tool_name: ToolName,
        exclude_fs: list[FilesystemType] = [],
    ):
        self.input_file_before = input_file_before
        self.input_file_after = input_file_after
        self.output_image = output_image
        self.title = title
        self.exclude_fs = exclude_fs

        result = self.__parse()
        self.__plot(result, self.title, tool_name)

    def __parse(self):
        result = []
        for path in FilesystemType:
            if path in self.exclude_fs:
                continue

            before = 0
            after = 0
            df_line_start = FS_MOUNT_POINTS[path]
            try:
                with open(f"fs/{path}/{self.input_file_before}") as f:
                    before = self.__df_results_read_file(f, df_line_start)

                with open(f"fs/{path}/{self.input_file_after}") as f:
                    after = self.__df_results_read_file(f, df_line_start)
                result.append(self.__DfResult(before, after, str(path)))

            except FileNotFoundError:
                logging.warning(f"Cannot read df file for '{path}'. Skipping")

        return result

    def __df_results_read_file(self, file, df_line_start):
        lines = []
        while line := file.readline():
            if df_line_start in line:
                lines.append(line)

        bytes_used = [int(line.split()[2]) for line in lines]
        return sum(bytes_used) / len(bytes_used)

    def __plot(self, results, title: str, tool_name: ToolName):
        x = [result.x() for result in results]
        y = [result.y() for result in results]
        xlabel = "File system"
        ylabel = "Space used (GB)"
        filename = self.output_image

        BarPlot(x, y, xlabel, ylabel, title, filename, tool_name, PlotUnit.SCALAR)


class BonnieBenchmark:
    output_html_path = GRAPHS_OUTPUT_DIR + "/html"
    output_tex = GRAPHS_OUTPUT_DIR + "/tex"
    output_csv = BONNIE_OUTPUT_DIR + "/bonnie++.csv"
    output_csv_all = BONNIE_OUTPUT_DIR + "/bonnie++_all.csv"
    output_html = output_html_path + "/bonnie-graphs.html"
    output_html_all = output_html_path + "/bonnie-graphs_all.html"
    tool_name = ToolName.BONNIE

    input_file = "out/bonnie/out.csv"

    def __init__(self):
        logging.info(
            f"Initializing bonnie graphing with input {self.input_file} and output {self.output_csv}, {self.output_html_path}"
        )
        create_dir(self.output_tex)
        create_dir(self.output_html_path)
        result_all = self.__parse()
        self.__save(result_all, self.output_csv_all)
        try:
            self.__generate_table(self.output_html_all, self.output_csv_all)
        except pd.errors.ParserError:
            logging.warning(f"Failed to generate bonnie table: {self.input_file}")
            return

        result = self.__parse([FilesystemType.NILFS_DEDUP])
        self.__save(result, self.output_csv)
        self.__generate_table(self.output_html, self.output_csv)
        self.__df()
        self.__test_configuration()

    def __parse(self, exclude: list[FilesystemType] = []):
        result = ""
        for path in FilesystemType:
            if path in exclude:
                continue

            with open(f"fs/{path}/{self.input_file}") as f:
                bonnie_output = ""
                while line := f.readline().rstrip():
                    bonnie_output += self.__convert_units(line)
                result += self.__merge_rows_into_average(bonnie_output)

        return result

    def __convert_units(self, row: str) -> str:
        splitted = row.split(",")

        for i, field in enumerate(splitted):
            # skip metadata and empty fields
            if i < 10:
                continue

            field = field.strip()

            if field == "" or field == "+++++" or field == "+++":
                splitted[i] = "0"

            if "us" in field:
                splitted[i] = str(int(field[:-2]) / 1000) + "ms"
            elif "ms" in field:
                splitted[i] = str(int(field[:-2])) + "ms"
            elif "s" in field:
                splitted[i] = str(int(field[:-1]) * 1000) + "ms"

        splitted[-1] = str(splitted[-1]) + "\n"

        return ",".join(splitted)

    def __merge_rows_into_average(self, rows):
        count = {}
        len_rows = 0
        for row in rows.split("\n"):
            if "format_version" in row:
                continue
            if row.strip() == "":
                continue

            len_rows += 1
            to_skip = 10
            for i, value in enumerate(row.split(",")):
                if to_skip > 0:
                    to_skip -= 1
                    count[i] = value
                elif "ms" in value:
                    if i not in count.keys():
                        count[i] = value
                    else:
                        count[i] = f"{int(float(count[i][:-2]) + float(value[:-2]))}ms"
                elif "+" in value or value == "":
                    count[i] = value
                else:
                    if i not in count.keys():
                        count[i] = float(value)
                    else:
                        if (
                            type(count[i]) is str
                        ):  # handle case when in the same column there are +++++ and normal values
                            count[i] = 0.0
                        count[i] = float(count[i]) + float(value)

        self.__average(len_rows, count)

        return "1.98" + ",".join([str(i) for i in count.values()]) + "\n"

    def __average(self, len_rows, count):
        to_skip = 10
        len_rows -= 1
        for i in count.keys():
            value = count[i]
            if to_skip > 0:
                to_skip -= 1
            elif isinstance(value, str):
                if "ms" in value:
                    count[i] = f"{round(float(count[i][:-2]) / (len_rows + 1), 1)}ms"
            else:
                count[i] = round(float(count[i]) / (len_rows + 1), 1)

    def __save(self, result, filename):
        with open(filename, "w") as f:
            f.write(result)

    def __generate_table(self, output_html, output_csv):
        df = self.__load_csv(output_csv)
        df = self.__convert_df_to_multidimentional(df)

        df.to_html(output_html)

        total_tables = 12
        columns_count = 2
        for i in range(0, total_tables * columns_count, columns_count):
            df_part = df.iloc[:, i : (i + columns_count)]
            name = f"bonnie{int(i / columns_count + 1)}"
            TexTable(df_part, name, ToolName.BONNIE).export()

    def __load_csv(self, filename):
        # CSV format taken from manual page bon_csv2html(1)
        #    FORMAT
        #    This is a list of the fields used in the CSV files  format  version  2.
        #    Format  version  1  was  the type used in Bonnie++ < 1.90.  Before each
        #    field I list the field number as well as the name given in the heading

        #    0 format_version
        #           Version of the output format in use (1.98)

        #    1 bonnie_version
        #           (1.98)

        #    2 name Machine Name

        #    3 concurrency
        #           The number of copies of each operation to be  run  at  the  same
        #           time

        #    4 seed Random number seed

        #    5 file_size
        #           Size in megs for the IO tests

        #    6 chunk_size
        #           Size of chunks in bytes

        #    7 seeks
        #           Number of seeks for random seek test

        #    8 seek_proc_count
        #           Number of seeker processes for the random seek test

        #    9 putc,putc_cpu
        #           Results for writing a character at a time K/s,%CPU

        #    11 put_block,put_block_cpu
        #           Results for writing a block at a time K/s,%CPU

        #    13 rewrite,rewrite_cpu
        #           Results for reading and re-writing a block at a time K/s,%CPU

        #    15 getc,getc_cpu
        #           Results for reading a character at a time K/s,%CPU

        #    17 get_block,get_block_cpu
        #           Results for reading a block at a time K/s,%CPU

        #    19 seeks,seeks_cpu
        #           Results for the seek test seeks/s,%CPU

        #    21 num_files
        #           Number of files for file-creation tests (units of 1024 files)

        #    22 max_size
        #           The  maximum size of files for file-creation tests.  Or the type
        #           of files for links.

        #    23 min_size
        #           The minimum size of files for file-creation tests.

        #    24 num_dirs
        #           The number of directories for creation of files in multiple  di‐
        #           rectories.

        #    25 file_chunk_size
        #           The size of blocks for writing multiple files.

        #    26 seq_create,seq_create_cpu
        #           Rate of creating files sequentially files/s,%CPU

        #    28 seq_stat,seq_stat_cpu
        #           Rate of reading/stating files sequentially files/s,%CPU

        #    30 seq_del,seq_del_cpu
        #           Rate of deleting files sequentially files/s,%CPU

        #    32 ran_create,ran_create_cpu
        #           Rate of creating files in random order files/s,%CPU

        #    34 ran_stat,ran_stat_cpu
        #           Rate of deleting files in random order files/s,%CPU

        #    36 ran_del,ran_del_cpu
        #           Rate of deleting files in random order files/s,%CPU

        #    38 putc_latency,put_block_latency,rewrite_latency
        #           Latency  (maximum  amount  of  time  for a single operation) for
        #           putc, put_block, and reqrite

        #    41 getc_latency,get_block_latency,seeks_latency
        #           Latency for getc, get_block, and seeks

        #    44 seq_create_latency,seq_stat_latency,seq_del_latency
        #           Latency for seq_create, seq_stat, and seq_del

        #    47 ran_create_latency,ran_stat_latency,ran_del_latency
        #           Latency for ran_create, ran_stat, and ran_del

        df = pd.read_csv(filename, header=None, dtype=object)
        bonnie_version_range = list(range(0, 2))
        bonnie_configuration_range = list(range(3, 9))
        bonnie_files_configuration_range = list(range(21, 26))
        bonnie_latency_range = list(range(38, 50))
        bonnie_exclude = (
            bonnie_version_range
            + bonnie_configuration_range
            + bonnie_files_configuration_range
            + bonnie_latency_range
        )

        df = df.drop(
            df.columns[bonnie_exclude],
            axis=1,
        )
        df.columns = [
            "Filesystem",
            "Character write K/s",
            "Character write %CPU",
            "Block write K/s",
            "Block write %CPU",
            "Block read, rewrite K/s",
            "Block read, rewrite %CPU",
            "Character read K/s",
            "Character read %CPU",
            "Block read K/s",
            "Block read %CPU",
            "Random seeks seeks/s",
            "Random seeks %CPU",
            "Sequential create files/s",
            "Sequential create %CPU",
            "Sequential read files/s",
            "Sequential read %CPU",
            "Sequential delete files/s",
            "Sequential delete %CPU",
            "Random create files/s",
            "Random create %CPU",
            "Random read files/s",
            "Random read %CPU",
            "Random delete files/s",
            "Random delete %CPU",
        ]
        return df

    def __convert_df_to_multidimentional(self, df):
        df = df[
            [
                "Filesystem",
                "Character write K/s",
                "Character write %CPU",
                "Block write K/s",
                "Block write %CPU",
                "Block read, rewrite K/s",
                "Block read, rewrite %CPU",
                "Character read K/s",
                "Character read %CPU",
                "Block read K/s",
                "Block read %CPU",
                "Random seeks seeks/s",
                "Random seeks %CPU",
                "Sequential create files/s",
                "Sequential create %CPU",
                "Sequential read files/s",
                "Sequential read %CPU",
                "Sequential delete files/s",
                "Sequential delete %CPU",
                "Random create files/s",
                "Random create %CPU",
                "Random read files/s",
                "Random read %CPU",
                "Random delete files/s",
                "Random delete %CPU",
            ]
        ]
        column_names = pd.DataFrame(
            [
                ["Character write", "KiB/s"],
                ["Character write", "\%CPU"],
                ["Block write", "KiB/s"],
                ["Block write", "\%CPU"],
                ["Block read, rewrite", "KiB/s"],
                ["Block read, rewrite", "\%CPU"],
                ["Character read", "KiB/s"],
                ["Character read", "\%CPU"],
                ["Block read", "KiB/s"],
                ["Block read", "\%CPU"],
                ["Random seeks", "seek/s"],
                ["Random seeks", "\%CPU"],
                ["Sequential create", "files/s"],
                ["Sequential create", "\%CPU"],
                ["Sequential read", "files/s"],
                ["Sequential read", "\%CPU"],
                ["Sequential delete", "files/s"],
                ["Sequential delete", "\%CPU"],
                ["Random create", "files/s"],
                ["Random create", "\%CPU"],
                ["Random read", "files/s"],
                ["Random read", "\%CPU"],
                ["Random delete", "files/s"],
                ["Random delete", "\%CPU"],
            ],
            columns=["Filesystem", ""],
        )

        columns = pd.MultiIndex.from_frame(column_names)

        df = df.set_index("Filesystem")
        df.columns = columns
        df.index.name = None
        return df

    def __df(self):
        logging.info("Generating df graphs for bonnie")
        input_file_before = "out/bonnie/df_before_bonnie.txt"
        input_file_after = "out/bonnie/df_after_bonnie.txt"
        output_image_name = "bonnie_metadata_size"
        title = "Space occupied after Bonnie++ test"

        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "bonnie_metadata_size_all"

        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
        )

    class __BonnieConfigType(Enum):
        SEED = "SEED"
        BLOCK_SIZE = "BLOCK_SIZE"
        BONNIE_NUMBER_OF_FILES = "BONNIE_NUMBER_OF_FILES"
        FILE_SIZE = "FILE_SIZE"
        RUNS = "BONNIE_RUNS"

    def __test_configuration(self):
        config = self.__test_configuration_read()
        df = self.__test_configuration_parse(config)
        self.__test_configuration_export(df)

    def __test_configuration_read(self):
        params = {}
        with open(BONNIE_CONFIG, "r") as f:
            for line in f.readlines():
                splitted = line.split("=")
                key = splitted[0].strip()
                if any(type.value in key for type in self.__BonnieConfigType):
                    # split to get two sides of expression
                    # ex. SEED=29047 -> params["SEED"] = 29047
                    value = splitted[1].strip()
                    params[key] = value

        return params

    def __test_configuration_parse(self, params):
        df = pd.DataFrame(
            {
                "Parameter": [
                    "seed",
                    "block size",
                    "file size",
                    "test runs",
                ],
                "Value": [
                    int(params[self.__BonnieConfigType.SEED.value]),
                    int(params[self.__BonnieConfigType.BLOCK_SIZE.value]),
                    params[self.__BonnieConfigType.FILE_SIZE.value],
                    params[self.__BonnieConfigType.RUNS.value],
                ],
            }
        )
        return df

    def __test_configuration_export(self, df):
        name = "bonnie_configuration"
        TexTable(df, name, ToolName.BONNIE, with_index=False).export()


class FioBenchmark:
    fio_log_dir = f"{OUTPUT_DIR}/fio/logs"
    data_dir = OUTPUT_DIR + "/fio/gnuplot"
    tool_name = ToolName.FIO
    log_dir = f"{LOG_DIR}/fio"
    tests = [
        "random_read_test",
        "random_write_test",
        "append_read_test",
        "append_write_test",
        "sequential_read_test",
        "sequential_write_test",
    ]

    def __init__(self):
        logging.info(f"Generating fio graphs from data dir {self.data_dir}")
        self.__generate_fio_data_from_logs()
        self.__fio()
        self.__df()
        self.__test_configuration()

    def __generate_fio_data_from_logs(self):
        self.__copy_fio_logs()
        self.__generate_gnuplot()

    def __copy_fio_logs(self):
        create_dir(self.fio_log_dir)
        logging.info(f"Copying fio logs to {self.fio_log_dir}")

        for filesystem in FilesystemType:
            fio_out_dir = f"fs/{filesystem}/out/fio"
            for subdir, _, files in os.walk(fio_out_dir):
                log_files = list(filter(lambda f: ".log" in f, files))
                with Pool() as pool:
                    pool.starmap(
                        FioBenchmark.copy_fio_log,
                        zip(
                            repeat(self.fio_log_dir),
                            repeat(subdir),
                            repeat(filesystem),
                            log_files,
                        ),
                    )

    def copy_fio_log(
        fio_log_dir: str, subdir: str, filesystem: FilesystemType, file: str
    ):
        src = os.path.join(subdir, file)
        dst = f"{fio_log_dir}/{filesystem}_{file}"
        logging.debug(f"Copying fio log: {src} -> {dst}")
        shutil.copy(src, dst)

    def __generate_gnuplot(self):
        logging.info(f"Generating gnuplot from fio logs for {self.tests}")
        with Pool() as pool:
            pool.starmap(
                FioBenchmark.generate_gnuplot_for_test,
                zip(
                    repeat(self.data_dir),
                    repeat(self.log_dir),
                    repeat(self.fio_log_dir),
                    self.tests,
                ),
            )

    def generate_gnuplot_for_test(
        data_dir: str, log_dir: str, fio_log_dir: str, test_name: str
    ):
        test_out_dir = f"{data_dir}/{test_name}"
        remove_dir(test_out_dir)
        create_dir(test_out_dir)
        create_dir(log_dir)
        log_file = f"{log_dir}/generate_fio_gnuplot_{test_name}.log"
        logging.debug(f"Generating gnuplot for test {test_name}, log file: {log_file}")
        f = open(log_file, "w+")

        subprocess.run(
            [
                "fio2gnuplot",
                "-t",
                test_name,
                "-d",
                test_out_dir,
                "-p",
                f"*{test_name}_bw*.log",
                "-v",
            ],
            stdout=f,
            stderr=f,
            cwd=fio_log_dir,
        )
        logging.debug(
            f"Finished generating gnuplot for test {test_name}, log file: {log_file}"
        )

    def __fio(self):
        logging.info("Generating fio bandwidth graphs")
        for subdir, _, files in os.walk(self.data_dir):
            for file in files:
                if "average" in file:
                    logging.info(f"Processing fio result file: {file}")
                    try:
                        self.__process(os.path.join(subdir, file))
                        self.__process_without_dedup(os.path.join(subdir, file))
                    except Exception:
                        logging.warning(f"Failed to process {file}")

    def __process(self, file_path: str):
        xx = []
        yy = []
        with open(file_path) as f:
            for line in f.readlines():
                splitted_line = line.strip().split(" ")
                if (
                    self.__does_list_contain_digit(splitted_line)
                    and len(splitted_line) == 2
                ):
                    throughput = int(splitted_line[1]) / 1000  # in megabytes / s
                    yy.append(throughput)
                elif len(splitted_line) == 6:
                    filesystem_name = splitted_line[5].split("_")[0]
                    xx.append(filesystem_name)

        self.__plot(xx, yy, file_path)

    def __plot(self, xx, yy, file_path):
        # ./output/fio/gnuplot/random_read_test_bw.average
        # Match this part     ^--------------^
        test_name = " ".join(file_path.split("/")[-1].split(".")[0].split("_")[:3])
        title = f"I/O Bandwidth for {test_name}"
        xlabel = "File system"
        ylabel = "Bandwidth (MB/s)"
        filename = f"{'_'.join(test_name.split(' '))}_average_bandwidth_all"
        BarPlot(
            xx, yy, xlabel, ylabel, title, filename, self.tool_name, PlotUnit.SCALAR
        )

    def __process_without_dedup(self, file_path: str):
        xx = []
        yy = []
        with open(file_path) as f:
            is_dedup = False
            for line in f.readlines():
                splitted_line = line.strip().split(" ")
                if (
                    self.__does_list_contain_digit(splitted_line)
                    and len(splitted_line) == 2
                ):
                    if is_dedup:
                        is_dedup = False
                        continue

                    throughput = int(splitted_line[1]) / 1000  # in megabytes / s
                    yy.append(throughput)
                elif len(splitted_line) == 6:
                    filesystem_name = splitted_line[5].split("_")[0]
                    if filesystem_name == FilesystemType.NILFS_DEDUP.value:
                        is_dedup = True
                        continue
                    xx.append(filesystem_name)

        self.__plot_without_dedup(xx, yy, file_path)

    def __plot_without_dedup(self, xx, yy, file_path):
        # ./output/fio/gnuplot/random_read_test_bw.average
        # Match this part     ^--------------^
        test_name = " ".join(file_path.split("/")[-1].split(".")[0].split("_")[:3])
        title = f"I/O Bandwidth for {test_name}"
        xlabel = "File system"
        ylabel = "Bandwidth (MB/s)"
        filename = f"{'_'.join(test_name.split(' '))}_average_bandwidth"
        BarPlot(
            xx, yy, xlabel, ylabel, title, filename, self.tool_name, PlotUnit.SCALAR
        )

    def __does_list_contain_digit(self, list):
        return len([s for s in list if s.isdigit()]) != 0

    def __df(self):
        logging.info("Generating df graphs for fio tests")
        out_dir = "out/fio"

        input_file_before = out_dir + "/df_before_fio_append_read_test.txt"
        input_file_after = out_dir + "/df_after_fio_append_read_test.txt"
        output_image_name = "fio_append_read_metadata_size"
        title = "Space occupied after append read test"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "fio_append_read_metadata_size_all"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
        )

        input_file_before = out_dir + "/df_before_fio_append_write_test.txt"
        input_file_after = out_dir + "/df_after_fio_append_write_test.txt"
        output_image_name = "fio_append_write_metadata_size"
        title = "Space occupied after fio append write test"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "fio_append_write_metadata_size_all"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
        )

        input_file_before = out_dir + "/df_before_fio_random_read_test.txt"
        input_file_after = out_dir + "/df_after_fio_random_read_test.txt"
        output_image_name = "fio_random_read_metadata_size"
        title = "Space occupied after fio random read test"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "fio_random_read_metadata_size_all"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
        )

        input_file_before = out_dir + "/df_before_fio_random_write_test.txt"
        input_file_after = out_dir + "/df_after_fio_random_write_test.txt"
        output_image_name = "fio_random_write_metadata_size"
        title = "Space occupied after fio random write test"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "fio_random_write_metadata_size_all"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
        )

        input_file_before = out_dir + "/df_before_fio_sequential_read_test.txt"
        input_file_after = out_dir + "/df_after_fio_sequential_read_test.txt"
        output_image_name = "fio_sequential_read_metadata_size"
        title = "Space occupied after sequential read test"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "fio_sequential_read_metadata_size_all"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
        )

        input_file_before = out_dir + "/df_before_fio_sequential_write_test.txt"
        input_file_after = out_dir + "/df_after_fio_sequential_write_test.txt"
        output_image_name = "fio_sequential_write_metadata_size"
        title = "Space occupied after sequential write test"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "fio_sequential_write_metadata_size_all"
        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            self.tool_name,
        )

    def __test_configuration(self):
        config = self.__test_configuration_read()
        df = self.__test_configuration_parse(config)
        self.__test_configuration_export(df)

    def __test_configuration_read(self):
        config = configparser.ConfigParser()
        logging.info(f"Reading fio config from {FIO_CONFIG}")
        config.read(FIO_CONFIG)
        return config

    def __test_configuration_parse(self, config) -> pd.DataFrame:
        size = config["global"]["size"]
        block_size = config["global"]["blocksize"]
        iodepth = int(config["global"]["iodepth"])
        ioengine = config["global"]["ioengine"]
        randseed = int(config["global"]["randseed"])
        allrandrepeat = "Yes" if config["global"]["allrandrepeat"] == "1" else "No"
        fsync_on_close = "Yes" if config["global"]["fsync_on_close"] == "1" else "No"
        end_fsync = "Yes" if config["global"]["end_fsync"] == "1" else "No"
        loops = int(config["global"]["loops"])

        df = pd.DataFrame(
            {
                "Parameter": [
                    "Random seed",
                    "All rand repeat",
                    "I/O engine",
                    "Concurrent I/O units",
                    "Block size",
                    "File size",
                    "Fsync on close",
                    "End fsync",
                    "Test runs",
                ],
                "Value": [
                    randseed,
                    allrandrepeat,
                    ioengine,
                    iodepth,
                    block_size,
                    size,
                    fsync_on_close,
                    end_fsync,
                    loops,
                ],
            },
        )

        return df

    def __test_configuration_export(self, df: pd.DataFrame):
        name = "fio_configuration"
        TexTable(df, name, ToolName.FIO, with_index=False).export()


class DedupDf:
    def __init__(
        self,
        fs_type: FilesystemType,
        tool_name: str,
        display_tool_name: str,
    ):
        logging.info("Generating df graphs from dedup tests")
        self.tool_name = tool_name
        self.display_tool_name = display_tool_name
        out_dir = f"fs/{fs_type}/out/dedup"
        file_pattern = f"_deduplication_{tool_name}"
        self.files = DfResult(out_dir, file_pattern, fs_type).files

        self.__generate_graphs_dedup_ratio()
        self.__generate_graphs_data_reduction()
        self.__generate_graphs_expected_reclaim()

    def __generate_graphs_dedup_ratio(self):
        title = f"{self.display_tool_name} space reduction ratio"
        filename = f"{self.tool_name}_dedup_ratio"
        xlabel = "File size"
        ylabel = "Space reduction ratio"
        self.__generate_graphs(
            title,
            filename,
            xlabel,
            ylabel,
            self.__calculate_deduplication_ratio,
            PlotUnit.PERCENT,
        )

    def __generate_graphs_data_reduction(self):
        title = f"{self.display_tool_name} space reduction"
        filename = f"{self.tool_name}_data_reduction"
        xlabel = "File size"
        ylabel = "Space reduction"
        self.__generate_graphs(
            title,
            filename,
            xlabel,
            ylabel,
            self.__calculate_data_reduction,
            PlotUnit.PERCENT,
        )

    def __generate_graphs_expected_reclaim(self):
        title = f"{self.display_tool_name} storage reclaim"
        filename = f"{self.tool_name}_storage_reclaim"
        xlabel = "File size (megabytes)"
        ylabel = "Storage reclaimed (megabytes)"
        self.__generate_graphs(
            title,
            filename,
            xlabel,
            ylabel,
            self.__calculate_storage_reclaim,
            PlotUnit.SCALAR,
        )

    def __generate_graphs(
        self, title, filename, xlabel, ylabel, y_func, plot_unit: PlotUnit
    ):
        logging.debug("Processing files for dedup tests")
        file_sizes = self.__classify_by_file_size()
        ordered_sizes = OrderedDict(
            sorted(file_sizes.items(), key=self.sort_by_size_without_postfix)
        )
        logging.debug(f"Gathered file_sizes: {file_sizes}")
        logging.debug(f"Gathered ordered_sizes: {ordered_sizes}")

        xx = []
        yy = []
        for entry in ordered_sizes:
            x, y = self.__xy_for_file_size(entry, ordered_sizes, y_func)
            xx.append(x)
            yy.append(y)

        BarPlot(xx, yy, xlabel, ylabel, title, filename, ToolName.DEDUP, plot_unit)

    def sort_by_size_without_postfix(self, key):
        size = key[0]
        return int(size[:-1])

    def __xy_for_file_size(self, key, sizes, y_func):
        x = key

        if len(sizes[key]) != 2:
            if len(sizes[key]) > 2:
                logging.warning("Multiple df files for the same test are not supported")
            elif len(sizes[key]) < 2:
                if sizes[key][0].type == DfFileType.BEFORE:
                    logging.warning(
                        f"Missing df after file, only before file is present: {sizes[key][0]}"
                    )
                else:
                    logging.warning(
                        f"Missing df before file, only after file is present: {sizes[key][0]}"
                    )
            return 0, 0

        before, after = sizes[key]
        if before.type == DfFileType.AFTER:
            before, after = after, before
        y = y_func(before.df_size.size, after.df_size.size)
        return x, y

    def __classify_by_file_size(self):
        file_sizes = {}
        for file in self.files:
            if file.file_size in file_sizes.keys():
                file_sizes[file.file_size].append(file)
            else:
                file_sizes[file.file_size] = [file]
        return file_sizes

    def __calculate_deduplication_ratio(self, before, after):
        return before / after

    def __calculate_data_reduction(self, before, after):
        return 1 - after / before

    def __calculate_storage_reclaim(self, before, after):
        return (before - after) / 1_000  # to mb


class DfResult:
    def __init__(self, out_dir: str, file_pattern: str, fs_type: FilesystemType):
        self.out_dir = out_dir
        self.files: list[DfFile] = []

        for _, _, files in os.walk(self.out_dir):
            for file in files:
                if file_pattern in file:
                    self.files.append(DfFile(self.out_dir, file, fs_type))


class DfFile:
    class __DfSize:
        def __init__(self, filepath: str, filesystem: FilesystemType):
            self.filepath = filepath
            self.filesystem = filesystem
            line = self.__extract_mountpoint_line()
            self.size = self.__extract_size(line)

        def __extract_mountpoint_line(self):
            with open(self.filepath) as f:
                for line in f.readlines():
                    line = line.strip().split()
                    mount_point = line[0]
                    fs_mount_point = FS_MOUNT_POINTS[self.filesystem]
                    if fs_mount_point == mount_point:
                        return line

        def __extract_size(self, line):
            return int(line[2])

        def __repr__(self):
            return f"""__DfSize: {{filepath = {self.filepath}, filesystem = {self.filesystem}, size = {self.size}}}"""

    def __init__(self, out_dir: str, filename: str, fs_type: FilesystemType):
        self.filename = filename
        raw_type = filename.strip().split("_")[1]
        if raw_type == DfFileType.BEFORE.value:
            self.type = DfFileType.BEFORE
        elif raw_type == DfFileType.AFTER.value:
            self.type = DfFileType.AFTER
        else:
            raise Exception(
                f"Invalid df file type: '{raw_type}', in file: '{filename}'"
            )
        # match -----------------v_v
        # df_after_deduplication_16M.txt
        self.prog_name = filename.strip().split("_")[3]
        self.file_size = filename.strip().split("_")[4].split(".")[0]
        filepath = f"{out_dir}/{self.filename}"
        self.df_size = DfFile.__DfSize(filepath, fs_type)

    def __repr__(self):
        return f"""DfFile: {{filename = {self.filename}, prog_name = {self.prog_name}, file_size = {self.file_size}, df_size = {{{self.df_size}}}}}"""


class DfFileType(Enum):
    BEFORE = "before"
    AFTER = "after"


class ResourceUtilization:
    def __init__(
        self,
        fs_type: FilesystemType,
        tool_name: str,
        display_tool_name: str,
    ):
        self.fs_type = fs_type
        self.tool_name = tool_name
        self.out_dir_jpg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.JPG}/dedup"
        self.out_dir_svg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.SVG}/dedup"

        self.display_tool_name = display_tool_name
        self.out_dir = f"fs/{fs_type}/out/dedup"
        self.files: list[ResourceUtilization.__ResourceUtilizationFile] = []
        self.__parse_files()
        if len(self.files) < 2:
            logging.warning(
                f"Couldn't parse resource utilization files in {self.out_dir}, skipping"
            )
            return
        self.__combine_files()

        self.__plot_elapsed_time()
        self.__plot_memory_usage()

    def __parse_files(self):
        logging.info(f"Parsing resource utilization files in {self.out_dir}")
        for _, _, files in os.walk(self.out_dir):
            for file in files:
                if f"time_{self.tool_name}_" in file:
                    logging.debug(f"Processing {file}")
                    self.files.append(
                        self.__ResourceUtilizationFile(self.out_dir, file)
                    )

    class ResourceUtilizationFields:
        def __str__(self):
            return str(self.value)

        REAL_TIME = "real-time"
        SYSTEM_TIME = "system-time"
        USER_TIME = "user-time"
        MAX_MEMORY = "max-memory"
        FILE_SIZE_M = "file-size-megabytes"

    class __ResourceUtilizationFile:
        def __init__(self, out_dir: str, filename: str):
            self.__path = f"{out_dir}/{filename}"
            self.df = pd.read_csv(self.__path)
            # get this part---v v
            # time_duperemove_64M.log
            size = filename.split("_")[2].split(".")[0]
            size_m = int(size[:-1])
            self.df[ResourceUtilization.ResourceUtilizationFields.FILE_SIZE_M] = size_m
            self.df = self.df.set_index(
                str(ResourceUtilization.ResourceUtilizationFields.FILE_SIZE_M)
            )
            self.df[ResourceUtilization.ResourceUtilizationFields.MAX_MEMORY] = self.df[
                ResourceUtilization.ResourceUtilizationFields.MAX_MEMORY
            ].transform(lambda m: m / 1000)

    def __combine_files(self):
        combined = pd.concat(map(lambda file: file.df, self.files))
        self.combined = combined.sort_values(
            ResourceUtilization.ResourceUtilizationFields.FILE_SIZE_M
        )

    def __plot_elapsed_time(self):
        ax = self.combined[
            [
                ResourceUtilization.ResourceUtilizationFields.SYSTEM_TIME,
                ResourceUtilization.ResourceUtilizationFields.USER_TIME,
            ]
        ].plot(
            kind="bar",
            stacked=True,
            title=f"{self.display_tool_name} deduplication time elapsed",
            xlabel="File size (megabytes)",
            ylabel="Elapsed time (seconds)",
        )
        legend = ax.get_legend()
        legend.get_texts()[0].set_text("system time")
        legend.get_texts()[1].set_text("user time")
        figure = ax.get_figure()
        out = f"{self.tool_name}_time_elapsed"
        out_jpg = f"{self.out_dir_jpg}/{out}.{FileExportType.JPG}"
        out_svg = f"{self.out_dir_svg}/{out}.{FileExportType.SVG}"
        figure.savefig(out_jpg, dpi=300, bbox_inches="tight")
        figure.savefig(out_svg, bbox_inches="tight")

    def __plot_memory_usage(self):
        ax = self.combined[
            [ResourceUtilization.ResourceUtilizationFields.MAX_MEMORY]
        ].plot(
            kind="bar",
            title=f"{self.display_tool_name} deduplication maximal memory usage",
            xlabel="File size (megabytes)",
            ylabel="Occupied memory (megabytes)",
            legend=None,
        )

        self.__plot_memory_usage_max(ax)

        out = f"{self.tool_name}_occupied_memory"
        out_jpg = f"{self.out_dir_jpg}/{out}.{FileExportType.JPG}"
        out_svg = f"{self.out_dir_svg}/{out}.{FileExportType.SVG}"
        figure = ax.get_figure()
        figure.savefig(out_jpg, dpi=300, bbox_inches="tight")
        figure.savefig(out_svg, bbox_inches="tight")

    def __plot_memory_usage_max(self, ax: plt.Axes):
        max = self.combined[
            ResourceUtilization.ResourceUtilizationFields.MAX_MEMORY
        ].max()
        xmin, xmax = ax.get_xlim()

        ax.hlines(y=max, xmin=xmin, xmax=xmax, color="red", linewidth=1)
        _, ymax = ax.get_ylim()
        label_position = max / ymax + 0.02
        ax.text(
            0.88,
            label_position,
            f"Maximum = {max:.1f}M",
            ha="right",
            va="center",
            transform=ax.transAxes,
            size=8,
            zorder=3,
        )


class DedupBenchmark:
    def __init__(self):
        self.__df()
        self.__resources()

    def __df(self):
        DedupDf(
            fs_type=FilesystemType.NILFS_DEDUP,
            tool_name="dedup",
            display_tool_name="Nilfs dedup",
        )
        DedupDf(
            fs_type=FilesystemType.BTRFS, tool_name="dduper", display_tool_name="dduper"
        )
        DedupDf(
            fs_type=FilesystemType.BTRFS,
            tool_name="duperemove",
            display_tool_name="duperemove",
        )

    def __resources(self):
        ResourceUtilization(
            fs_type=FilesystemType.NILFS_DEDUP,
            tool_name="nilfs-dedup",
            display_tool_name="Nilfs dedup",
        )
        ResourceUtilization(
            fs_type=FilesystemType.BTRFS, tool_name="dduper", display_tool_name="dduper"
        )
        ResourceUtilization(
            fs_type=FilesystemType.BTRFS,
            tool_name="duperemove",
            display_tool_name="duperemove",
        )


class DeleteBenchmark:
    def __init__(self):
        logging.info("Generating df graphs for delete test")
        input_file_before = "out/delete/df_before_delete_test.txt"
        input_file_after = "out/delete/df_after_delete_test.txt"
        output_image_name = "delete_metadata_size"
        title = "Space occupied after deletion test"

        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            ToolName.DELETE,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "delete_metadata_size_all"

        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            ToolName.DELETE,
        )


class AppendBenchmark:
    def __init__(self):
        logging.info("Generating df graphs for append test")
        input_file_before = "out/append/df_before_append_test.txt"
        input_file_after = "out/append/df_after_append_test.txt"
        output_image_name = "append_metadata_size"
        title = "Space occupied after append test"

        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            ToolName.APPEND,
            [FilesystemType.NILFS_DEDUP],
        )

        output_image_name = "append_metadata_size_all"

        SpaceUsageDf(
            input_file_before,
            input_file_after,
            output_image_name,
            title,
            ToolName.APPEND,
        )


def create_dir(dir_name: str):
    logging.debug(f"Creating directory {dir_name}")
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def remove_dir(dir_name: str):
    logging.debug(f"Removing directory {dir_name}")
    try:
        shutil.rmtree(dir_name)
    except FileNotFoundError:
        logging.debug(f"Directory {dir_name} does not exist, skipping deletion")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(f"{LOG_DIR}/graphs.log"),
            logging.StreamHandler(),
        ],
    )


def create_output_dirs():
    create_dir(LOG_DIR)
    create_dir(OUTPUT_DIR)
    create_dir(GRAPHS_OUTPUT_DIR)
    create_dir(BONNIE_OUTPUT_DIR)


def main():
    configure_logging()

    logging.info("START")

    create_output_dirs()

    BonnieBenchmark()
    DeleteBenchmark()
    AppendBenchmark()
    FioBenchmark()
    DedupBenchmark()

    logging.info("END")


if __name__ == "__main__":
    main()
