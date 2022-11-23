#!/usr/bin/env python3

paths = ["./btrfs", "./copyfs", "./ext4", "./nilfs", "./waybackfs"]


def main():
    result = ""
    result_all = ""

    for path in paths:
        with open(f"{path}/out/out.csv") as f:
            current_output = ""
            while line := f.readline().rstrip():
                current_output += read_row(line)
            result += average(current_output)
            result_all += current_output

    with open("bonnie++.csv", "w") as f:
        f.write(result)

    with open("all-bonnie++.csv", "w") as f:
        f.write(result_all)


def read_row(row: str) -> str:
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


def average(rows):
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
                    count[i] = float(count[i]) + float(value)

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

    return "1.98" + ",".join([str(i) for i in count.values()]) + "\n"


if __name__ == "__main__":
    main()


# class BonnieResult:
#     pass


# class StorageResult:
#     def __init__(self, before: float, after: float):
#         self.used_space = after - before


# class Result:
#     def __init__(self, bonnie: BonnieResult, storage: StorageResult):
#         self.bonnie = bonnie
#         self.storage = storage


# def main():
#     data = {}
#     data["copyfs"] = copyfs()
#     plot(data)

# def plot(data):
#     print(data)

# def copyfs() -> Result:
#     root_dir = "./copyfs/out"
#     for subdir, dirs, files in os.walk(root_dir):
#         if len(dirs) == 0:
#             continue
#         before = parse_df_on(dirs, root_dir, "/dev/sda1", "df_before.txt")
#         after = parse_df_on(dirs, root_dir, "/dev/sda1", "df_after.txt")
#         storage = StorageResult(before, after)
#         bonnie = BonnieResult(parse_bonnie(dirs, root_dir))
#         # only one output dir is expected, so return after first iteration
#         return Result(bonnie, storage)


# def parse_df_on(dirs, root_dir, pattern: str, file_name: str) -> float:
#     bytes = 0
#     for dir in dirs:
#         with open(f"{root_dir}/{dir}/{file_name}", "r") as f:
#             lines = f.readlines()
#             for line in lines:
#                 if re.search(pattern, line) is not None:
#                     bytes += int(line.split()[3])
#     return bytes / len(dirs)


# def parse_bonnie(dirs, root_dir) -> str:
#     file_name = "out.csv"
#     header = r"Output Format, Bonnie++ Version, Machine Name, Concurrency Level, Random Number Seed, File Size, Chunk Size, Character Writes (K/s),Character Writes (% cpu), Block Writes (K/s),Block Writes (% cpu), Reading/Rewriting Block (K/s),Reading/Rewriting Block (% cpu), Character Reads (K/s),Character Reads (% cpu), Block Reads (K/s),Block Reads (% cpu), Seek (s/s),Seek (% cpu), Number of files (units of 1024), Max file size, Min file size, Number of dirs, Block size for writing multiple files, Rate of sequential file creation (f/s),Rate of sequential file creation (% cpu), Rate of sequential file reads (f/s),Rate of sequential file reads (% cpu), Rate of sequential file deletion (f/s), (% cpu), Rate of random file creates (f/s),Rate of random file creates (% cpu), Rate of random file reads (f/s),Rate of random file reads (% cpu), Rate of random file deletes (f/s),Rate of random file deletes (% cpu), Character Write Latency, Block Write Latency, Rewrite Latency, Character Read Latency, Block Read Latency, Seek Latency, Latency for sequential write, Latency for sequential stat, Latency for sequential delete, Latency for random create, Latency for random stat, Latency for random delete"
#     header = [name.strip() for name in header.split(',')]
#     print("HEADER: ", len(header))
#     # print(header)
#     for dir in dirs:
#         df = pd.read_csv(f"{root_dir}/{dir}/{file_name}", names=header)
#         print(df)
#     return None


# if __name__ == "__main__":
#     main()
