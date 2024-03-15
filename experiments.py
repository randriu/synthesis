import paynt.cli
import os



def main():
    directory = 'experiment-models'
    max_mem = 2
    for mem in range(1,max_mem+1):
        for filename in os.scandir(directory):
            if filename.is_file():
                head, tail = os.path.split(filename.path)
                new_filepath = os.path.join('/home/vojta/FIT/DP/synthesis/outputs', tail + f"-{mem}.txt")
                f = open(new_filepath, "w")
                os.system(f"python3 paynt.py --project {head} --sketch {tail} --pomdp-memory-size {mem} --profiling | tee {new_filepath}")
                print("head",head)

    # os.system(f"python3 paynt.py --project experiment-models --sketch recycling.dpomdp --use-new-split-method --pomdp-memory-size  --profiling | tee recycling.dpomdp-3.txt")
    # os.system(f"python3 paynt.py --project experiment-models --sketch 2generals.dpomdp --use-new-split-method --pomdp-memory-size 3 --profiling | tee 2generals.dpomdp-3.txt")

if __name__ == "__main__":
    main()