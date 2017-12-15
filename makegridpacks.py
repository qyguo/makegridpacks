#!/usr/bin/env python

import argparse, os, sys, urllib

from helperstuff import allsamples

def makegridpacks(dryrun):
  for sample in allsamples():
    print sample, sample.makegridpack()
    sys.stdout.flush()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-n", "--dry-run", action="store_true")
  args = parser.parse_args()
  makegridpacks(dryrun=args.dry_run)
