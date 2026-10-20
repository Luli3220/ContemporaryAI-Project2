"""Rebuild tables, figures and report using the current raw batch only."""
import argparse
from .aggregate import aggregate
from .analysis import analyze
from .batch import BASE, write_manifest


def rebuild(root):
    aggregate(root)
    analyze(root)
    from .plot_results import plot_all
    plot_all(root)
    if root==BASE/'results':
        from .write_report import write_report
        write_report(root)
    write_manifest(root)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick',action='store_true')
    args=parser.parse_args()
    rebuild(BASE/'results/quick' if args.quick else BASE/'results')
    from .audit_results import audit
    audit(BASE/'results/quick' if args.quick else BASE/'results')
