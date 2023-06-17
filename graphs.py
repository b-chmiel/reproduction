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
import logging
import pandas as pd
import configparser
import argparse


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
    BONNIE_ALL = "bonnie-all"
    FIO = "fio"
    DEDUP = "dedup"


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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler(f"{LOG_DIR}/graphs.log"))
logger.addHandler(logging.StreamHandler())


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
        logger.info(
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
        logger.info(f"Exporting latex table to {filename}")
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
                logger.warning(f"Cannot read df file for '{path}'. Skipping")

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
        logger.info(
            f"Initializing bonnie graphing with input {self.input_file} and output {self.output_csv}, {self.output_html_path}"
        )
        create_dir(self.output_tex)
        create_dir(self.output_html_path)
        result_all = self.__parse()
        self.__save(result_all, self.output_csv_all)
        try:
            self.__generate_table(
                self.output_html_all, self.output_csv_all, ToolName.BONNIE_ALL
            )
        except pd.errors.ParserError:
            logger.warning(f"Failed to generate bonnie table: {self.input_file}")
            return

        result = self.__parse([FilesystemType.NILFS_DEDUP])
        self.__save(result, self.output_csv)
        self.__generate_table(self.output_html, self.output_csv, ToolName.BONNIE)
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

    def __generate_table(self, output_html, output_csv, tool_name: ToolName):
        df = self.__load_csv(output_csv)
        df = self.__convert_df_to_multidimentional(df)

        df.to_html(output_html)

        total_tables = 12
        columns_count = 2
        for i in range(0, total_tables * columns_count, columns_count):
            df_part = df.iloc[:, i : (i + columns_count)]
            name = f"bonnie{int(i / columns_count + 1)}"
            TexTable(df_part, name, tool_name).export()

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
        logger.info("Generating df graphs for bonnie")
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
        "sequential_read_test",
        "sequential_write_test",
    ]

    def __init__(self):
        logger.info(f"Generating fio graphs from data dir {self.data_dir}")
        self.__generate_fio_data_from_logs()
        self.__fio()
        self.__df()
        self.__test_configuration()

    def __generate_fio_data_from_logs(self):
        self.__copy_fio_logs()
        self.__generate_gnuplot()

    def __copy_fio_logs(self):
        create_dir(self.fio_log_dir)
        logger.info(f"Copying fio logs to {self.fio_log_dir}")

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

    @staticmethod
    def copy_fio_log(
        fio_log_dir: str, subdir: str, filesystem: FilesystemType, file: str
    ):
        src = os.path.join(subdir, file)
        dst = f"{fio_log_dir}/{filesystem}_{file}"
        logger.debug(f"Copying fio log: {src} -> {dst}")
        shutil.copy(src, dst)

    def __generate_gnuplot(self):
        logger.info(f"Generating gnuplot from fio logs for {self.tests}")
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

    @staticmethod
    def generate_gnuplot_for_test(
        data_dir: str, log_dir: str, fio_log_dir: str, test_name: str
    ):
        test_out_dir = f"{data_dir}/{test_name}"
        remove_dir(test_out_dir)
        create_dir(test_out_dir)
        create_dir(log_dir)
        log_file = f"{log_dir}/generate_fio_gnuplot_{test_name}.log"
        logger.debug(f"Generating gnuplot for test {test_name}, log file: {log_file}")
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
        logger.debug(
            f"Finished generating gnuplot for test {test_name}, log file: {log_file}"
        )

    def __fio(self):
        logger.info("Generating fio bandwidth graphs")
        for subdir, _, files in os.walk(self.data_dir):
            for file in files:
                if "average" in file:
                    logger.info(f"Processing fio result file: {file}")
                    try:
                        self.__process(os.path.join(subdir, file))
                        self.__process_without_dedup(os.path.join(subdir, file))
                    except Exception:
                        logger.warning(f"Failed to process {file}")

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
        logger.info("Generating df graphs for fio tests")
        out_dir = "out/fio"

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
        logger.info(f"Reading fio config from {FIO_CONFIG}")
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


class WhenType(StrEnum):
    BEFORE = "before"
    AFTER = "after"


class DedupDf:
    out_dir_jpg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.JPG}/dedup"
    out_dir_svg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.SVG}/dedup"

    def __init__(
        self,
        fs_type: FilesystemType,
        tool_name: str,
        display_tool_name: str,
        out_dir: str,
    ):
        logger.info("Generating df graphs from dedup tests")
        self.tool_name = tool_name
        self.display_tool_name = display_tool_name
        out_dir = f"fs/{fs_type}/out/{out_dir}"
        file_pattern = f"_deduplication_{tool_name}"
        self.files_df = DfResult(out_dir, file_pattern, fs_type).df

        create_dir(self.out_dir_jpg)
        create_dir(self.out_dir_svg)

        self.__plot_dedup_ratio()
        self.__plot_data_reduction()
        self.__plot_reclaim()
        self.__plot_expected_reclaim()

    def __plot_dedup_ratio(self):
        title = f"{self.display_tool_name} space reduction ratio"
        filename = f"{self.tool_name}_dedup_ratio"
        xlabel = "File size"
        ylabel = "Space reduction ratio"
        self.__plot(
            title, filename, xlabel, ylabel, self.__calculate_deduplication_ratio
        )

    def __plot_data_reduction(self):
        title = f"{self.display_tool_name} space reduction"
        filename = f"{self.tool_name}_data_reduction"
        xlabel = "File size"
        ylabel = "Space reduction"
        self.__plot(title, filename, xlabel, ylabel, self.__calculate_data_reduction)

    def __plot_reclaim(self):
        logger.debug("Generating DedupDdf reclaim graph")
        title = f"{self.display_tool_name} storage reclaim"
        filename = f"{self.tool_name}_storage_reclaim"
        xlabel = "File size (megabytes)"
        ylabel = "Storage reclaimed (megabytes)"
        self.__plot(title, filename, xlabel, ylabel, self.__calculate_storage_reclaim)

    def __plot_expected_reclaim(self):
        logger.debug("Generating DedupDdf expected reclaim graph")
        title = f"{self.display_tool_name} expected storage reclaim"
        filename = f"{self.tool_name}_expected_storage_reclaim"
        xlabel = "File size (megabytes)"
        ylabel = "Storage reclaimed (megabytes)"

        df = self.files_df.sort_values(DfResult.Schema.FILE_SIZE_MEGABYTES)
        df = df.pivot(
            index=DfResult.Schema.FILE_SIZE_MEGABYTES,
            columns=DfResult.Schema.TYPE,
            values=DfResult.Schema.SIZE,
        )
        df["actual"] = self.__calculate_storage_reclaim(
            df[WhenType.BEFORE], df[WhenType.AFTER]
        )
        df["expected"] = df.index

        ax = df[["actual", "expected"]].plot(
            kind="bar", title=title, xlabel=xlabel, ylabel=ylabel
        )
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, labels)
        ax.locator_params(nbins=10)
        ax.tick_params(axis="x", rotation=0)

        out_jpg = f"{self.out_dir_jpg}/{filename}.{FileExportType.JPG}"
        out_svg = f"{self.out_dir_svg}/{filename}.{FileExportType.SVG}"
        logger.info(f"Exporting DedupDf graphs: {out_jpg}, {out_svg}")

        figure = ax.get_figure()
        figure.savefig(out_jpg, dpi=300, bbox_inches="tight")
        figure.savefig(out_svg, bbox_inches="tight")

    def __plot_expected_reclaim_expected_line(self, ax, df: pd.DataFrame):
        max = df[GnuTimeFile.Fields.MAX_MEMORY.value].max()
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

    def __plot(self, title, filename, xlabel, ylabel, y_func):
        logger.debug("Processing files for dedup tests")
        df = self.files_df.sort_values(DfResult.Schema.FILE_SIZE_MEGABYTES)
        df = df.pivot(
            index=DfResult.Schema.FILE_SIZE_MEGABYTES,
            columns=DfResult.Schema.TYPE,
            values=DfResult.Schema.SIZE,
        )
        df["value"] = y_func(df[WhenType.BEFORE], df[WhenType.AFTER])
        ax = df[["value"]].plot(
            kind="bar", title=title, xlabel=xlabel, ylabel=ylabel, legend=None
        )
        ax.locator_params(nbins=10)
        ax.tick_params(axis="x", rotation=0)
        figure = ax.get_figure()
        out_jpg = f"{self.out_dir_jpg}/{filename}.{FileExportType.JPG}"
        out_svg = f"{self.out_dir_svg}/{filename}.{FileExportType.SVG}"
        logger.info(f"Exporting DedupDf graphs: {out_jpg}, {out_svg}")
        figure.savefig(out_jpg, dpi=300, bbox_inches="tight")
        figure.savefig(out_svg, bbox_inches="tight")

    @staticmethod
    def __calculate_deduplication_ratio(before, after):
        return before / after

    @staticmethod
    def __calculate_data_reduction(before, after):
        return 1 - after / before

    @staticmethod
    def __calculate_storage_reclaim(before, after):
        return (before - after) / 1_000  # to mb


class DfResult:
    class Schema(StrEnum):
        FS_TYPE = "fs_type"
        SIZE = "size"
        PROG_NAME = "prog_name"
        TYPE = "type"
        FILE_SIZE_MEGABYTES = "file_size_megabytes"

    def __init__(self, out_dir: str, file_pattern: str, fs_type: FilesystemType):
        self.df = pd.DataFrame()

        for _, _, files in os.walk(out_dir):
            for file in files:
                if file_pattern in file:
                    self.df = pd.concat(
                        [self.df, DfResult.__DfFile(out_dir, file, fs_type).df]
                    )

    class __DfFile:
        def __init__(self, out_dir: str, filename: str, fs_type: FilesystemType):
            self.__filename = filename
            self.__filepath = f"{out_dir}/{self.__filename}"
            self.__fs_type = fs_type
            self.__size = self.__extract_size()

            raw_type = filename.strip().split("_")[1]
            if raw_type == WhenType.BEFORE.value:
                self.__type = WhenType.BEFORE
            elif raw_type == WhenType.AFTER.value:
                self.__type = WhenType.AFTER
            else:
                raise Exception(
                    f"Invalid df file type: '{raw_type}', in file: '{filename}'"
                )
            # match -----------------v___v
            # df_after_deduplication_dedup_16M.txt

            self.__prog_name = filename.strip().split("_")[3]

            # match -----------------------v_v
            # df_after_deduplication_dedup_16M.txt
            self.__file_size = filename.strip().split("_")[4].split(".")[0]

            self.df = pd.DataFrame(
                {
                    DfResult.Schema.FS_TYPE: [self.__fs_type],
                    DfResult.Schema.SIZE: [self.__size],
                    DfResult.Schema.PROG_NAME: [self.__prog_name],
                    DfResult.Schema.TYPE: [self.__type],
                    DfResult.Schema.FILE_SIZE_MEGABYTES: [self.__file_size],
                }
            )
            self.df[DfResult.Schema.FILE_SIZE_MEGABYTES] = (
                self.df[DfResult.Schema.FILE_SIZE_MEGABYTES]
                .str.removesuffix("M")
                .astype("int")
            )

        def __extract_size(self):
            line = self.__extract_mountpoint_line()
            return int(line[2])

        def __extract_mountpoint_line(self):
            with open(self.__filepath) as f:
                for line in f.readlines():
                    line = line.strip().split()
                    mount_point = line[0]
                    fs_mount_point = FS_MOUNT_POINTS[self.__fs_type]
                    if fs_mount_point == mount_point:
                        return line

        def __repr__(self):
            return f"""DfFile: {{filename = {self.__filename}, prog_name = {self.__prog_name}, file_size = {self.__file_size}}}"""


class GnuTimeFile:
    class Fields(Enum):
        def __str__(self):
            return str(self.value)

        REAL_TIME = "real-time"
        SYSTEM_TIME = "system-time"
        USER_TIME = "user-time"
        MAX_MEMORY = "max-memory"
        FILE_SIZE = "file-size"
        FILE_NAME = "file-name"
        WHEN = "when"

    def __init__(self, path: str):
        self.df = pd.read_csv(path)
        self.__format()

    def __format(self):
        self.__format_file_size()
        self.__format_max_memory()

    def __format_file_size(self):
        self.df[GnuTimeFile.Fields.FILE_SIZE.value] = (
            self.df[GnuTimeFile.Fields.FILE_SIZE.value]
            .str.removesuffix("M")
            .astype("int")
        )
        self.df = self.df.set_index(GnuTimeFile.Fields.FILE_SIZE.value)

    def __format_max_memory(self):
        self.df[GnuTimeFile.Fields.MAX_MEMORY.value] = (
            self.df[GnuTimeFile.Fields.MAX_MEMORY.value] / 1000
        )


class DedupGnuTime:
    out_dir_jpg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.JPG}/dedup"
    out_dir_svg = f"{GRAPHS_OUTPUT_DIR}/{FileExportType.SVG}/dedup"

    def __init__(
        self,
        fs_type: FilesystemType,
        tool_name: str,
        display_tool_name: str,
        out_dir: str,
    ):
        self.tool_name = tool_name
        create_dir(self.out_dir_jpg)
        create_dir(self.out_dir_svg)

        self.display_tool_name = display_tool_name
        self.out_dir = f"fs/{fs_type}/out/{out_dir}"

        self.__plot_memory_usage()
        self.__plot_time_elapsed()
        self.__plot_csum_validate()

    def __plot_memory_usage(self):
        self.__plot_memory_usage_comparison()
        self.__plot_memory_usage_detailed()

    def __plot_memory_usage_comparison(self):
        pass

    def __plot_memory_usage_detailed(self):
        df = GnuTimeFile(path=f"{self.out_dir}/time-whole.csv").df
        ax = df[[GnuTimeFile.Fields.MAX_MEMORY.value]].plot(
            kind="bar",
            title=f"{self.display_tool_name} deduplication maximal memory usage",
            xlabel="File size (megabytes)",
            ylabel="Occupied memory (megabytes)",
            legend=None,
        )
        ax.locator_params(nbins=10)
        ax.tick_params(axis="x", rotation=0)

        self.__plot_memory_usage_max(ax, df)

        out = f"{self.tool_name}_occupied_memory"
        out_jpg = f"{self.out_dir_jpg}/{out}.{FileExportType.JPG}"
        out_svg = f"{self.out_dir_svg}/{out}.{FileExportType.SVG}"
        figure = ax.get_figure()
        logger.info(
            f"Exporting DedupGnuTime usage detailed graphs: {out_jpg}, {out_svg}"
        )
        figure.savefig(out_jpg, dpi=300, bbox_inches="tight")
        figure.savefig(out_svg, bbox_inches="tight")

    def __plot_memory_usage_max(self, ax, df: pd.DataFrame):
        max = df[GnuTimeFile.Fields.MAX_MEMORY.value].max()
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

    def __plot_time_elapsed(self):
        df = GnuTimeFile(path=f"{self.out_dir}/time-whole.csv").df
        ax = df[
            [
                GnuTimeFile.Fields.SYSTEM_TIME.value,
                GnuTimeFile.Fields.USER_TIME.value,
            ]
        ].plot(
            kind="bar",
            stacked=True,
            title=f"{self.display_tool_name} deduplication time elapsed",
            xlabel="File size (megabytes)",
            ylabel="Elapsed time (seconds)",
        )
        ax.locator_params(nbins=10)
        ax.tick_params(axis="x", rotation=0)
        legend = ax.get_legend()
        legend.get_texts()[0].set_text("system time")
        legend.get_texts()[1].set_text("user time")
        figure = ax.get_figure()
        out = f"{self.tool_name}_time_elapsed"
        out_jpg = f"{self.out_dir_jpg}/{out}.{FileExportType.JPG}"
        out_svg = f"{self.out_dir_svg}/{out}.{FileExportType.SVG}"
        logger.info(f"Exporting DedupGnuTime time_elapsed graphs: {out_jpg}, {out_svg}")
        figure.savefig(out_jpg, dpi=300, bbox_inches="tight")
        figure.savefig(out_svg, bbox_inches="tight")

    def __plot_csum_validate(self):
        pass
        # df = pd.read_csv(f"{self.out_dir}/time-csum-validate.csv")
        # df[GnuTimeFile.Fields.FILE_SIZE.value] = df[
        #     GnuTimeFile.Fields.FILE_SIZE.value
        # ].str.removesuffix("M")
        # df[GnuTimeFile.Fields.FILE_SIZE.value] = df[
        #     GnuTimeFile.Fields.FILE_SIZE.value
        # ].astype("int")
        # df = df.set_index(GnuTimeFile.Fields.FILE_SIZE.value)
        # print(df)
        # df_before = df[df[GnuTimeFile.Fields.WHEN.value] == WhenType.BEFORE.value]
        # df_before = df_before.groupby([GnuTimeFile.Fields.FILE_SIZE.value]).agg(
        #     {f"{GnuTimeFile.Fields.REAL_TIME.value}": ["mean"]}
        # )
        # df_before["Before"] = df_before.iloc[:, [0]]
        # df_before = df_before.drop(columns=[GnuTimeFile.Fields.REAL_TIME.value])

        # df_after = df[df[GnuTimeFile.Fields.WHEN.value] == WhenType.AFTER.value]
        # df_after = df_after.groupby([GnuTimeFile.Fields.FILE_SIZE.value]).agg(
        #     {f"{GnuTimeFile.Fields.REAL_TIME.value}": ["mean"]}
        # )
        # df_after["After"] = df_after.iloc[:, [0]]
        # df_after = df_after.drop(columns=[GnuTimeFile.Fields.REAL_TIME.value])

        # merged = pd.merge(
        #     df_before, df_after, how="left", on=GnuTimeFile.Fields.FILE_SIZE.value
        # )
        # merged = merged.sort_values(GnuTimeFile.Fields.FILE_SIZE.value)
        # print(merged)
        # ax = merged.plot()
        # figure = ax.get_figure()
        # figure.savefig("tmp.jpg", dpi=300)

        # print(df_before)
        # print(df_after)
        # ax = df[[
        #     GnuTimeFile.Fields.REAL_TIME.value
        # ]]


class DedupBenchmark:
    def __init__(self):
        self.__df()
        self.__gnu_time()

    def __df(self):
        DedupDf(
            fs_type=FilesystemType.NILFS_DEDUP,
            tool_name="dedup",
            display_tool_name="Nilfs dedup",
            out_dir="dedup/dedup",
        )
        DedupDf(
            fs_type=FilesystemType.BTRFS,
            tool_name="dduper",
            display_tool_name="dduper",
            out_dir="dedup/dduper",
        )
        DedupDf(
            fs_type=FilesystemType.BTRFS,
            tool_name="duperemove",
            display_tool_name="duperemove",
            out_dir="dedup/duperemove",
        )

    def __gnu_time(self):
        DedupGnuTime(
            fs_type=FilesystemType.NILFS_DEDUP,
            tool_name="dedup",
            display_tool_name="Nilfs dedup",
            out_dir="dedup/dedup",
        )
        DedupGnuTime(
            fs_type=FilesystemType.BTRFS,
            tool_name="dduper",
            display_tool_name="dduper",
            out_dir="dedup/dduper",
        )
        DedupGnuTime(
            fs_type=FilesystemType.BTRFS,
            tool_name="duperemove",
            display_tool_name="duperemove",
            out_dir="dedup/duperemove",
        )


def create_dir(dir_name: str):
    logger.debug(f"Creating directory {dir_name}")
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def remove_dir(dir_name: str):
    logger.debug(f"Removing directory {dir_name}")
    try:
        shutil.rmtree(dir_name)
    except FileNotFoundError:
        logger.debug(f"Directory {dir_name} does not exist, skipping deletion")


def create_output_dirs():
    create_dir(LOG_DIR)
    create_dir(OUTPUT_DIR)
    create_dir(GRAPHS_OUTPUT_DIR)
    create_dir(BONNIE_OUTPUT_DIR)


class ArgBenchmark(StrEnum):
    BONNIE = "bonnie"
    FIO = "fio"
    DEDUP = "dedup"
    ALL = "all"


def parse_args() -> ArgBenchmark:
    parser = argparse.ArgumentParser(prog="graphs")
    parser.add_argument(
        "-b",
        "--benchmark",
        choices=[
            ArgBenchmark.BONNIE,
            ArgBenchmark.FIO,
            ArgBenchmark.DEDUP,
            ArgBenchmark.ALL,
        ],
        default=ArgBenchmark.ALL,
        required=False,
    )
    args = parser.parse_args()
    return args.benchmark


def main():
    logger.info("START")

    create_output_dirs()

    match parse_args():
        case ArgBenchmark.BONNIE:
            BonnieBenchmark()
        case ArgBenchmark.FIO:
            FioBenchmark()
        case ArgBenchmark.DEDUP:
            DedupBenchmark()
        case ArgBenchmark.ALL:
            BonnieBenchmark()
            FioBenchmark()
            DedupBenchmark()

    logger.info("END")


if __name__ == "__main__":
    main()
