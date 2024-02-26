import paynt.cli
import os



def main():
    directory = 'experiment-models'
    max_mem = 3
    for mem in range(3,max_mem+1):
        for filename in os.scandir(directory):
            if filename.is_file():
                head, tail = os.path.split(filename.path)
                new_filepath = os.path.join('/home/vojta/FIT/DP/synthesis/outputs', tail + f"-{mem}.txt")
                f = open(new_filepath, "w")
                os.system(f"python3 paynt.py --project {head} --sketch {tail} --pomdp-memory-size {mem} | tee {new_filepath}")

if __name__ == "__main__":
    main()