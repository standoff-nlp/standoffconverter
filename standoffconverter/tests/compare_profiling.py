import click
import pandas as pd
from pathlib import Path
from dateutil import parser
import numpy as np
import plotext as plt

def parse_and_sort_profiling_files():
    p = Path('profiling')
    dates = []
    fnames = []
    for f in p.iterdir():
        if f.suffix == '.pkl':
            dates.append(
                parser.isoparse(f.stem.replace('_', ':'))
            )
            fnames.append(f)
    sorter = np.argsort(dates)
    return np.array(fnames)[sorter].tolist()
    
    
@click.command()
@click.option('--filea')
@click.option('--fileb')
def main(filea, fileb):

    if filea is None:
        # take the second most recent
        profiling_files = parse_and_sort_profiling_files()
        filea = profiling_files[-2]

    if fileb is None:
        # take the most recent
        profiling_files = parse_and_sort_profiling_files()
        fileb = profiling_files[-1]

    profile_a = pd.read_pickle(filea)
    profile_b = pd.read_pickle(fileb)

    merged = pd.merge(
        profile_a, 
        profile_b, 
        how='left',
        on=['document_length','document_depth', 'working_depth', 'item_length']
    )


    plt.clp()
    bins = 30
    plt.hist(merged['tottime_x'], bins, label="profile a")
    plt.hist(merged['tottime_y'], bins, label="profile b")
    plt.title("tottime distribution")
    plt.xlabel("time bins")
    plt.ylabel("frequency")
    plt.canvas_color("none")
    plt.axes_color("none")
    plt.ticks_color("cloud")
    plt.figsize(50, 15)
    plt.show()

    merged['diff'] = merged['tottime_x'] - merged['tottime_y']
    print("")
    print(f"## avg improvement: {merged['diff'].mean()} seconds ##")
    print("")


if __name__ == '__main__':
    main()

