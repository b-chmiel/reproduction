#!/usr/bin/env python3

from enum import Enum
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import subprocess
import os
from numbers import Number
from collections import OrderedDict
import logging


class FilesystemType(Enum):
    BTRFS = "btrfs"
    COPYFS = "copyfs"
    NILFS = "nilfs"
    NILFS_DEDUP = "nilfs-dedup"
    WAYBACKFS = "waybackfs"


FS_MOUNT_POINTS = {
    FilesystemType.BTRFS: "/dev/loop0",
    FilesystemType.COPYFS: "/dev/sda1",
    FilesystemType.NILFS: "/dev/loop0",
    FilesystemType.NILFS_DEDUP: "/dev/loop0",
    FilesystemType.WAYBACKFS: "/dev/sda1",
}

OUTPUT_DIR = "./output"
GRAPHS_OUTPUT_DIR = OUTPUT_DIR + "/graphs"
BONNIE_OUTPUT_DIR = OUTPUT_DIR + "/bonnie"


class PlotExportType(Enum):
    SVG = "svg"
    JPG = "jpg"


class BarPlot:
    out_dir_jpg = f"{GRAPHS_OUTPUT_DIR}/{PlotExportType.JPG.value}"
    out_dir_svg = f"{GRAPHS_OUTPUT_DIR}/{PlotExportType.SVG.value}"

    def __init__(
        self,
        x: list[str],
        y: list[Number],
        xlabel: str,
        ylabel: str,
        title: str,
        filename: str,
    ):
        self.x = x
        self.y = y
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.filename = filename
        create_dir(self.out_dir_jpg)
        create_dir(self.out_dir_svg)

    def plot(self):
        out_jpg = f"{self.out_dir_jpg}/{self.filename}.{PlotExportType.JPG.value}"
        out_svg = f"{self.out_dir_svg}/{self.filename}.{PlotExportType.SVG.value}"

        logging.info(f"Generating BarPlot: {out_jpg}, {out_svg}")
        plt.bar(np.arange(len(self.y)), self.y, color="blue", edgecolor="black")
        plt.xticks(np.arange(len(self.y)), self.x)
        plt.xlabel(self.xlabel, fontsize=16)
        plt.ylabel(self.ylabel, fontsize=16)
        plt.title(self.title, fontsize=16)
        plt.savefig(out_jpg, dpi=300)
        plt.savefig(out_svg)
        plt.cla()


class Bonnie:
    output_csv = BONNIE_OUTPUT_DIR + "/bonnie++.csv"
    output_csv_all = BONNIE_OUTPUT_DIR + "/bonnie++_all.csv"
    output_html = GRAPHS_OUTPUT_DIR + "/bonnie-graphs.html"
    output_html_all = GRAPHS_OUTPUT_DIR + "/bonnie-graphs_all.html"

    input_file = "out/bonnie/out.csv"

    def __init__(self):
        logging.info(
            f"Initializing bonnie graphing with input {self.input_file} and output {self.output_csv}, {self.output_html}"
        )
        result_all = self.__parse()
        self.__save(result_all, self.output_csv_all)
        self.__generate_table(self.output_html_all, self.output_csv_all)

        result = self.__parse([FilesystemType.NILFS_DEDUP])
        self.__save(result, self.output_csv)
        self.__generate_table(self.output_html, self.output_csv)

    def __parse(self, exclude: list[FilesystemType] = []):
        result = ""
        for path in FilesystemType:
            if path in exclude:
                continue

            with open(f"fs/{path.value}/{self.input_file}") as f:
                bonnie_output = ""
                while line := f.readline().rstrip():
                    bonnie_output += self.__convert_units(line)
                result += self.__merge_rows_into_average(bonnie_output)

        return result

    def __convert_units(self, row: str) -> str:
        splitted = row.split(",")

        for i, field in enumerate(splitted):
            # skip metadata and empty fields
            if i < 10 or field == "" or field == "+++++" or field == "+++":
                continue

            if "us" in field:
                field = field.strip()
                splitted[i] = str(int(field[:-2]) / 1000) + "ms"

            if "ms" in field:
                field = field.strip()
                splitted[i] = str(int(field[:-2])) + "ms"

        splitted[-1] = str(splitted[-1]) + "\n"

        return ",".join(splitted)

    def __merge_rows_into_average(self, rows):
        count = {}
        len_rows = 0
        for row in rows.split("\n"):
            if "format_version" in row:
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
                    count[i] = f"{float(count[i][:-2]) / len_rows}ms"
            else:
                count[i] = float(count[i]) / len_rows

    def __save(self, result, filename):
        with open(filename, "w") as f:
            f.write(result)

    def __generate_table(self, filename, output_csv):
        with open(filename, "w+") as graphs_html:
            subprocess.call(["bon_csv2html", output_csv], stdout=graphs_html)


class Df:
    class DfPlot:
        pass

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
        exclude_fs: list[FilesystemType] = [],
    ):
        self.input_file_before = input_file_before
        self.input_file_after = input_file_after
        self.output_image = output_image
        self.title = title
        self.exclude_fs = exclude_fs

        result = self.__parse()
        self.__plot(result, self.title)

    def __parse(self):
        result = []
        for path in FilesystemType:
            if path in self.exclude_fs:
                continue

            before = 0
            after = 0
            df_line_start = FS_MOUNT_POINTS[path]
            try:
                with open(f"fs/{path.value}/{self.input_file_before}") as f:
                    before = self.__df_results_read_file(f, df_line_start)

                with open(f"fs/{path.value}/{self.input_file_after}") as f:
                    after = self.__df_results_read_file(f, df_line_start)
                result.append(self.__DfResult(before, after, path.value))

            except FileNotFoundError:
                logging.warning(f"Cannot read df file for '{path.value}'. Skipping")

        return result

    def __df_results_read_file(self, file, df_line_start):
        lines = []
        while line := file.readline():
            if df_line_start in line:
                lines.append(line)

        bytes_used = [int(line.split()[2]) for line in lines]
        return sum(bytes_used) / len(bytes_used)

    def __plot(self, results, title: str):
        x = [result.x() for result in results]
        y = [result.y() for result in results]
        xlabel = "File system"
        ylabel = "Space used (GB)"
        filename = self.output_image

        p = BarPlot(x, y, xlabel, ylabel, title, filename)
        p.plot()


class Fio:
    data_dir = OUTPUT_DIR + "/fio/gnuplot"

    def __init__(self):
        logging.info(f"Generating fio graphs from data dir {self.data_dir}")
        for subdir, dirs, files in os.walk(self.data_dir):
            for file in files:
                if "average" in file:
                    logging.info(f"Processing fio result file: {file}")
                    self.__process(os.path.join(subdir, file))
                    self.__process_without_dedup(os.path.join(subdir, file))

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
                    xx.append(splitted_line[5].split("_")[0])

        self.__plot(xx, yy, file_path)

    def __plot(self, xx, yy, file_path):
        # ./build/fio/gnuplot/random_read_test_bw.average
        # Match this part     ^--------------^
        test_name = " ".join(file_path.split("/")[-1].split(".")[0].split("_")[:3])
        title = f"I/O Bandwidth for {test_name}"
        xlabel = "File system"
        ylabel = "Throughput (MB/s)"
        filename = f"{'_'.join(test_name.split(' '))}_average_bandwidth_all"
        p = BarPlot(xx, yy, xlabel, ylabel, title, filename)
        p.plot()

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
        # ./build/fio/gnuplot/random_read_test_bw.average
        # Match this part     ^--------------^
        test_name = " ".join(file_path.split("/")[-1].split(".")[0].split("_")[:3])
        title = f"I/O Bandwidth for {test_name}"
        xlabel = "File system"
        ylabel = "Throughput (MB/s)"
        filename = f"{'_'.join(test_name.split(' '))}_average_bandwidth"
        p = BarPlot(xx, yy, xlabel, ylabel, title, filename)
        p.plot()

    def __does_list_contain_digit(self, list):
        return len([s for s in list if s.isdigit()]) != 0


class DfSize:
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
        return f"""DfSize: {{filepath = {self.filepath}, filesystem = {self.filesystem}, size = {self.size}}}"""


class DedupDf:
    def __init__(
        self,
        plot_title: str,
        plot_filename: str,
        fs_type: FilesystemType,
        tool_name: str,
    ):
        logging.info("Generating df graphs from dedup tests")
        self.plot_title = plot_title
        self.plot_filename = plot_filename
        self.files: list[self.DedupDfFile] = []
        self.tool_name = tool_name

        self.out_dir = f"fs/{fs_type.value}/out/dedup"
        for _, _, files in os.walk(self.out_dir):
            for file in files:
                if tool_name in file:
                    self.files.append(self.DedupDfFile(self.out_dir, file, fs_type))
        self.__process_files()

    def sort_by_size_without_postfix(self, key):
        size = key[0]
        return int(size[:-1])

    def __process_files(self):
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
            x, y = self.__xy_for_file_size(entry, ordered_sizes)
            xx.append(x)
            yy.append(y)

        p = BarPlot(
            xx,
            yy,
            "File size",
            "Deduplication ratio",
            self.plot_title,
            self.plot_filename,
        )
        p.plot()

    def __xy_for_file_size(self, key, sizes):
        x = key

        if len(sizes[key]) != 2:
            if len(sizes[key]) > 2:
                logging.warning("Multiple df files for the same test are not supported")
            elif len(sizes[key]) < 2:
                if sizes[key][0].type == DedupDf.DedupDfFileType.BEFORE:
                    logging.warning(
                        f"Missing df after file, only before file is present: {sizes[key][0]}"
                    )
                else:
                    logging.warning(
                        f"Missing df before file, only after file is present: {sizes[key][0]}"
                    )
            return 0, 0

        before, after = sizes[key]
        if before.type == DedupDf.DedupDfFileType.AFTER:
            before, after = after, before
        y = self.__deduplication_ratio(before.df_size.size, after.df_size.size)
        return x, y

    def __classify_by_file_size(self):
        file_sizes = {}
        for file in self.files:
            if file.file_size in file_sizes.keys():
                file_sizes[file.file_size].append(file)
            else:
                file_sizes[file.file_size] = [file]
        return file_sizes

    def __deduplication_ratio(self, before, after):
        return before / after

    class DedupDfFileType(Enum):
        BEFORE = "before"
        AFTER = "after"

    class DedupDfFile:
        def __init__(self, out_dir: str, filename: str, fs_type: FilesystemType):
            self.filename = filename
            raw_type = filename.strip().split("_")[1]
            if raw_type == DedupDf.DedupDfFileType.BEFORE.value:
                self.type = DedupDf.DedupDfFileType.BEFORE
            elif raw_type == DedupDf.DedupDfFileType.AFTER.value:
                self.type = DedupDf.DedupDfFileType.AFTER
            else:
                raise Exception(
                    f"Invalid df file type: '{raw_type}', in file: '{filename}'"
                )
            # match -----------------v_v
            # df_after_deduplication_16M.txt
            self.prog_name = filename.strip().split("_")[3]
            self.file_size = filename.strip().split("_")[4].split(".")[0]
            filepath = f"{out_dir}/{self.filename}"
            self.df_size = DfSize(filepath, fs_type)

        def __repr__(self):
            return f"""DedupDfFile: {{filename = {self.filename}, prog_name = {self.prog_name}, file_size = {self.file_size}, df_size = {{{self.df_size}}}}}"""


def create_dir(dir_name: str):
    logging.debug(f"Creating directory {dir_name}")
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def bonnie_df():
    logging.info("Generating df graphs for bonnie")
    input_file_before = "out/bonnie/df_before_bonnie.txt"
    input_file_after = "out/bonnie/df_after_bonnie.txt"
    output_image_name = "bonnie_metadata_size"
    title = "Space occupied after bonnie++ test"

    Df(
        input_file_before,
        input_file_after,
        output_image_name,
        title,
        [FilesystemType.NILFS_DEDUP],
    )

    output_image_name = "bonnie_metadata_size_all"

    Df(input_file_before, input_file_after, output_image_name, title)


def delete_df():
    logging.info("Generating df graphs for delete test")
    input_file_before = "out/delete/df_before_delete_test.txt"
    input_file_after = "out/delete/df_after_delete_test.txt"
    output_image_name = "delete_metadata_size"
    title = "Space occupied after deletion test"

    Df(
        input_file_before,
        input_file_after,
        output_image_name,
        title,
        [FilesystemType.NILFS_DEDUP],
    )

    output_image_name = "delete_metadata_size_all"

    Df(input_file_before, input_file_after, output_image_name, title)


def fio_df():
    logging.info("Generating df graphs for fio tests")
    out_dir = "out/fio"

    input_file_before = out_dir + "/df_before_fio_file_append_read_test.txt"
    input_file_after = out_dir + "/df_after_fio_file_append_read_test.txt"
    output_image_name = "fio_file_append_read_metadata_size"
    title = "Space occupied after fio append read test"
    Df(
        input_file_before,
        input_file_after,
        output_image_name,
        title,
        [FilesystemType.NILFS_DEDUP],
    )

    output_image_name = "fio_file_append_read_metadata_size_all"
    Df(input_file_before, input_file_after, output_image_name, title)

    input_file_before = out_dir + "/df_before_fio_file_append_write_test.txt"
    input_file_after = out_dir + "/df_after_fio_file_append_write_test.txt"
    output_image_name = "fio_file_append_write_metadata_size"
    title = "Space occupied after fio append write test"
    Df(
        input_file_before,
        input_file_after,
        output_image_name,
        title,
        [FilesystemType.NILFS_DEDUP],
    )

    output_image_name = "fio_file_append_write_metadata_size_all"
    Df(input_file_before, input_file_after, output_image_name, title)

    input_file_before = out_dir + "/df_before_fio_random_read_test.txt"
    input_file_after = out_dir + "/df_after_fio_random_read_test.txt"
    output_image_name = "fio_random_read_metadata_size"
    title = "Space occupied after fio read test"
    Df(
        input_file_before,
        input_file_after,
        output_image_name,
        title,
        [FilesystemType.NILFS_DEDUP],
    )

    output_image_name = "fio_random_read_metadata_size_all"
    Df(input_file_before, input_file_after, output_image_name, title)

    input_file_before = out_dir + "/df_before_fio_random_write_test.txt"
    input_file_after = out_dir + "/df_after_fio_random_write_test.txt"
    output_image_name = "fio_random_write_metadata_size"
    title = "Space occupied after fio write test"
    Df(
        input_file_before,
        input_file_after,
        output_image_name,
        title,
        [FilesystemType.NILFS_DEDUP],
    )

    output_image_name = "fio_random_write_metadata_size_all"
    Df(input_file_before, input_file_after, output_image_name, title)


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler("logs/graphs.log"), logging.StreamHandler()],
    )


def create_output_dirs():
    create_dir(OUTPUT_DIR)
    create_dir(GRAPHS_OUTPUT_DIR)
    create_dir(BONNIE_OUTPUT_DIR)


def main():
    configure_logging()

    logging.info("START")

    create_output_dirs()

    Bonnie()
    bonnie_df()
    delete_df()
    fio_df()
    Fio()
    DedupDf(
        plot_title="Nilfs dedup deduplication ratio for different file sizes",
        plot_filename="nilfs_dedup_dedup_ratio",
        fs_type=FilesystemType.NILFS_DEDUP,
        tool_name="dedup",
    )
    DedupDf(
        plot_title="Dduper deduplication ratio for different file sizes",
        plot_filename="dduper_dedup_ratio",
        fs_type=FilesystemType.BTRFS,
        tool_name="dduper",
    )
    DedupDf(
        plot_title="Duperemove deduplication ratio for different file sizes",
        plot_filename="duperemove_dedup_ratio",
        fs_type=FilesystemType.BTRFS,
        tool_name="duperemove",
    )
    logging.info("END")


if __name__ == "__main__":
    main()
