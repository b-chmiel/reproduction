#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import subprocess

PATHS = ["./copyfs", "./ext4", "./nilfs", "./waybackfs"]
BUILD_DIR = "./build"

class Bonnie:
    output_csv = BUILD_DIR + "/bonnie++.csv"
    output_all_csv = BUILD_DIR + "/all-bonnie++.csv"
    output_html = BUILD_DIR + "/graphs.html"
    input_file = "out/bonnie/out.csv" 

    def __init__(self):
        result = ""
        result_all = ""

        for path in PATHS:
            with open(f"{path}/{self.input_file}") as f:
                current_output = ""
                while line := f.readline().rstrip():
                    current_output += self.__read_row(line)
                result += self.__parse(current_output)
                result_all += current_output

        with open(self.output_csv, "w") as f:
            f.write(result)

        with open(self.output_all_csv, "w") as f:
            f.write(result_all)

        graphs_html = open(self.output_html, "w+")
        subprocess.call(["bon_csv2html", self.output_csv], stdout=graphs_html)
    

    def __read_row(self, row: str) -> str:
        splitted = row.split(",")

        for i, field in enumerate(splitted):
            # skip metadata and empty fields
            if i < 10 or field == "" or field == "+++++" or field == "+++":
                continue

            if "ms" in field:
                field = field.strip()
                # convert millis to micros
                splitted[i] = str(int(field[:-2]) * 1000) + "us"

        splitted[-1] = str(splitted[-1]) + "\n"

        return ",".join(splitted)


    def __parse(self, rows):
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
                elif "us" in value:
                    if i not in count.keys():
                        count[i] = value
                    else:
                        count[i] = f"{int(int(count[i][:-2]) + int(value[:-2]))}us"
                elif "+" in value or value == "":
                    count[i] = value
                else:
                    if i not in count.keys():
                        count[i] = float(value)
                    else:
                        if type(count[i]) is str: # handle case when in the same column there are +++++ and normal values
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
                if "us" in value:
                    count[i] = f"{int(int(count[i][:-2]) / len_rows)}us"
            else:
                count[i] = int(float(count[i]) / len_rows)


class Df:
    class __DfResult:
        def __init__(self, before, after, name):
            self.before = before
            self.after = after
            self.name = name
        
        def x(self):
            return self.name
        
        def y(self):
            return self.after - self.before

    def __init__(self, input_file_before, input_file_after, output_image, title):
        self.input_file_before = input_file_before
        self.input_file_after = input_file_after
        self.output_image = output_image
        self.title = title

        result = []
        df_lines = {'./copyfs': '/dev/sda1', './ext4': '/dev/sda1', './nilfs': '/dev/loop0', './waybackfs': '/dev/sda1'}
        for path in PATHS:
            before = 0
            after = 0
            df_line_start = df_lines[path]
            with open(f"{path}/{self.input_file_before}") as f:
                before = self.__df_results_read_file(f, df_line_start)

            with open(f"{path}/{self.input_file_after}") as f:
                after = self.__df_results_read_file(f, df_line_start)

            result.append(self.__DfResult(before, after, path[2:]))
        
        self.__df_plot(result, self.title)

    def __df_results_read_file(self, file, df_line_start):
        lines = []
        while line := file.readline():
            if df_line_start in line:
                lines.append(line)
        
        bytes_used = [int(line.split()[2]) for line in lines]
        return sum(bytes_used) / len(bytes_used)

    def __df_plot(self, results, title):
        x = [result.x() for result in results]
        y = [result.y() for result in results]
        plt.bar(np.arange(len(y)), y ,color='blue',edgecolor='black')
        plt.xticks(np.arange(len(y)), x)
        plt.xlabel('File system', fontsize=16)
        plt.ylabel('Space used in bytes', fontsize=16)
        plt.title(title, fontsize=16)
        plt.savefig(self.output_image)
        plt.cla()


def create_build_dir():
    Path(BUILD_DIR).mkdir(parents=True, exist_ok=True)


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
    input_file_before = out_dir + "/df_before_fio_file_append_test.txt"
    input_file_after = out_dir + "/df_after_fio_file_append_test.txt"
    output_image = BUILD_DIR + "/fio_file_append_metadata_size.jpg"
    title = "Space occupied by metadata after fio file append test"
    Df(input_file_before, input_file_after, output_image, title)

    input_file_before = out_dir + "/df_before_fio_random_read_test.txt"
    input_file_after = out_dir + "/df_after_fio_random_read_test.txt"
    output_image = BUILD_DIR + "/fio_random_read_metadata_size.jpg"
    title = "Space occupied by metadata after fio random read test"
    Df(input_file_before, input_file_after, output_image, title)

    input_file_before = out_dir + "/df_before_fio_random_write_test.txt"
    input_file_after = out_dir + "/df_after_fio_random_write_test.txt"
    output_image = BUILD_DIR + "/fio_random_write_metadata_size.jpg"
    title = "Space occupied by metadata after fio random write test"
    Df(input_file_before, input_file_after, output_image, title)


def main():
    create_build_dir()
    Bonnie()
    bonnie_df()
    delete_df()
    fio_df()


if __name__ == "__main__":
    main()
