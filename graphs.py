#!/usr/bin/env python3

import matplotlib.pyplot as plt  # type:ignore

import numpy as np
from pathlib import Path
import subprocess
import os
from numbers import Number

PATHS = ["./copyfs", "./nilfs", "./waybackfs"]
BUILD_DIR = "./build"


class Plot:
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

    def plot(self):
        plt.bar(np.arange(len(self.y)), self.y, color="blue", edgecolor="black")
        plt.xticks(np.arange(len(self.y)), self.x)
        plt.xlabel(self.xlabel, fontsize=16)
        plt.ylabel(self.ylabel, fontsize=16)
        plt.title(self.title, fontsize=16)
        plt.savefig(self.filename)
        plt.cla()


class Bonnie:
    output_csv = BUILD_DIR + "/bonnie/bonnie++.csv"
    output_html = BUILD_DIR + "/bonnie/bonnie-graphs.html"
    input_file = "out/bonnie/out.csv"

    def __init__(self):
        result = self.__parse()
        self.__save(result)
        self.__generate_table()

    def __parse(self):
        result = ""
        for path in PATHS:
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
        result = ""
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

    def __save(self, result):
        with open(self.output_csv, "w") as f:
            f.write(result)

    def __generate_table(self):
        graphs_html = open(self.output_html, "w+")
        subprocess.call(["bon_csv2html", self.output_csv], stdout=graphs_html)


class Df:
    class __DfResult:
        def __init__(self, before, after, name):
            self.before = before
            self.after = after
            self.name = name

        def x(self):
            return self.name

        def y(self):
            return (self.after - self.before) / 1000_000  # in gigabytes

    def __init__(self, input_file_before, input_file_after, output_image, title):
        self.input_file_before = input_file_before
        self.input_file_after = input_file_after
        self.output_image = output_image
        self.title = title

        result = self.__parse()
        self.__plot(result, self.title)

    def __parse(self):
        result = []
        df_lines = {
            "./copyfs": "/dev/sda1",
            "./nilfs": "/dev/loop0",
            "./waybackfs": "/dev/sda1",
        }
        for path in PATHS:
            before = 0
            after = 0
            df_line_start = df_lines[path]
            try:
                with open(f"fs/{path}/{self.input_file_before}") as f:
                    before = self.__df_results_read_file(f, df_line_start)

                with open(f"fs/{path}/{self.input_file_after}") as f:
                    after = self.__df_results_read_file(f, df_line_start)
                result.append(self.__DfResult(before, after, path[2:]))

            except FileNotFoundError:
                print(f"Cannot read df file for '{path}'. Skipping")

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

        p = Plot(x, y, xlabel, ylabel, title, filename)
        p.plot()


class Fio:
    data_dir = BUILD_DIR + "/fio/gnuplot"

    def __init__(self):
        for subdir, dirs, files in os.walk(self.data_dir):
            for file in files:
                if "average" in file:
                    print("Processing: ", file)
                    self.__process(os.path.join(subdir, file))

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
        # Match this part    ^--------------^
        test_name = " ".join(file_path.split("/")[-1].split(".")[0].split("_")[:3])
        title = f"I/O Bandwidth for {test_name} test"
        xlabel = "File system"
        ylabel = "Throughput (MB/s)"
        filename = f"{BUILD_DIR}/{'_'.join(test_name.split(' '))}_average_bandwidth"
        # self.__plot(xx, yy, title, xlabel, ylabel, filename)
        p = Plot(xx, yy, xlabel, ylabel, title, filename)
        p.plot()

    def __does_list_contain_digit(self, list):
        return len([s for s in list if s.isdigit()]) != 0


def create_dir(dir_name: str):
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def bonnie_df():
    input_file_before = "out/bonnie/df_before_bonnie.txt"
    input_file_after = "out/bonnie/df_after_bonnie.txt"
    output_image = BUILD_DIR + "/bonnie_metadata_size.jpg"
    title = "Space occupied by metadata after bonnie++ test"

    Df(input_file_before, input_file_after, output_image, title)


def delete_df():
    input_file_before = "out/delete/df_before_delete_test.txt"
    input_file_after = "out/delete/df_after_delete_test.txt"
    output_image = BUILD_DIR + "/delete_metadata_size.jpg"
    title = "Space occupied by metadata after deletion test"

    Df(input_file_before, input_file_after, output_image, title)


def fio_df():
    out_dir = "out/fio"

    input_file_before = out_dir + "/df_before_fio_file_append_read_test.txt"
    input_file_after = out_dir + "/df_after_fio_file_append_read_test.txt"
    output_image = BUILD_DIR + "/fio_file_append_read_metadata_size.jpg"
    title = "Space occupied by metadata after fio file append read test"
    Df(input_file_before, input_file_after, output_image, title)

    input_file_before = out_dir + "/df_before_fio_file_append_write_test.txt"
    input_file_after = out_dir + "/df_after_fio_file_append_write_test.txt"
    output_image = BUILD_DIR + "/fio_file_append_write_metadata_size.jpg"
    title = "Space occupied by metadata after fio file append write test"
    Df(input_file_before, input_file_after, output_image, title)

    input_file_before = out_dir + "/df_before_fio_random_read_test.txt"
    input_file_after = out_dir + "/df_after_fio_random_read_test.txt"
    output_image = BUILD_DIR + "/fio_random_read_metadata_size.jpg"
    title = "Space occupied by metadata after fio read test"
    Df(input_file_before, input_file_after, output_image, title)

    input_file_before = out_dir + "/df_before_fio_random_write_test.txt"
    input_file_after = out_dir + "/df_after_fio_random_write_test.txt"
    output_image = BUILD_DIR + "/fio_random_write_metadata_size.jpg"
    title = "Space occupied by metadata after fio write test"
    Df(input_file_before, input_file_after, output_image, title)


def main():
    create_dir(BUILD_DIR)
    create_dir(BUILD_DIR + "/bonnie")
    Bonnie()
    bonnie_df()
    delete_df()
    fio_df()
    Fio()


if __name__ == "__main__":
    main()
