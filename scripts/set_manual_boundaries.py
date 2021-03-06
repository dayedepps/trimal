#!/usr/bin/python

#
# 'set_manual_boundaries.py'
#
#   Script implemented to work with trimAl to analyze gaps statistics and decide
#   which are the boundaries in a given alignment - columns inbetween these
#   boundaries will not be removed independently of the trimming strategy
#   selected.
#
#   [2014] S. Capella-Gutierrez - scapella@crg.es
#
#   this script is free software: you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free
#   Software Foundation, the last available version.
#
#   this script is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#   FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#   more details on <http://www.gnu.org/licenses/>
#

import os
import sys
import argparse
from string import strip

def main():

  parser = argparse.ArgumentParser()

  parser.add_argument("-i", "--input", dest = "inFile", required = True,
    type = str, help = "Output file containing gaps stats generated by trimAl"
    + " - option -sgc")

  parser.add_argument("--min_gapscore_allowed", dest = "minGapBoundaries", \
    type = float, default = .8, help = "Set the minimum gap score (1 - fraction"
      + "of gaps) which we will use to set the boundaries when there are not "
      + "two columns with no gaps - default 0.8")

  parser.add_argument("--get_best_boundaries", dest = "bestBoundaries", default
    = False, action = "store_true", help = "Get the best possible boundaries")

  parser.add_argument("--discard_nogaps_columns", dest = "discardNoGaps",
    default = False, action = "store_true", help = "Discard those columns with"
    + "no gaps - otherwise, those columns will be preferentially selected as "
    + "boundaries - this parameter will be ignored if this column are the first"
    + "/last one to pass the input gap_score threshold")

  parser.add_argument("--one_line", dest = "oneLine", default = False, action =
    "store_true", help = "Generate output in just one line which will be used "
      + "directly by trimAl")

  args = parser.parse_args()

  if not os.path.isfile(args.inFile):
    sys.exit("ERROR: The input file should be defined")

  if args.minGapBoundaries < 0 or args.minGapBoundaries > 1:
    sys.exit("ERROR: --min_gapscore_allow should be defined in the range [0,1]")

  npos = 0
  putative = [0, 0, False, 0, 0]
  boundaries = [-1, -1, -1, -1, -1, -1]
  for line in open(args.inFile, "rU"):
    ## Discard any line containing text
    if line[0] in ["#", "|", "+"]:
      continue

    f = [chunk for chunk in map(strip, line.split("\t")) if chunk]
    if not f:
      continue
    npos += 1
    pos = int(f[0])
    gap_score = float(f[2])

    ## This function is intended to find columns - with at least one gap - which
    ## will be used as left and right boundaries for trimAl
    if gap_score >= args.minGapBoundaries:

      ## Check whether the left boundary is defined, if that the case, define
      ## the right one
      if boundaries[0] != -1:
        ## We update constantently the right boundary until the last best value
        ## is found
        if gap_score != 1.0:
          boundaries[3] = pos
          boundaries[4] = gap_score

      ## Define the left boundary as the first value passing the input threshold
      elif gap_score != 1.0:
        boundaries[0] = pos
        boundaries[1] = gap_score

      ## Get the most to the right column without any gap
      if gap_score == 1.0:
        boundaries[5] = pos

      ## Get the most to the left column without any gap
      if gap_score == 1.0 and boundaries[2] == -1:
        boundaries[2] = pos

    else:
      ## Try to get the best potential cutting points below to the input
      ## thresholds - it would be useful if we don't found the boundaries

      ## We will update the right boundary constantly
      if gap_score > putative[4]:
          putative[4] = gap_score
          putative[3] = pos

      ## We update current value until the left boundary is found
      if boundaries[0] == -1:

        ## Any pick on values - reflected like the at least the double of the
        ## current best value, should be store.
        if gap_score > (2 * putative[1]):
          putative[1] = gap_score
          putative[2] = False
          putative[0] = pos

        ## We update the left boundaries if and only if the immediate previous
        ## position has at least a similar value
        if not putative[2] and gap_score >= putative[1]:
          putative[1] = gap_score
          putative[0] = pos
        else:
          putative[2] = True

  output = ""
  ## Generate output, if any

  ## First try to get the best column possible - unless the user has set-up
  ## specifically to discard them
  if boundaries[2] != boundaries[5] and not args.discardNoGaps:
    if not args.oneLine:
      ratio = float(boundaries[2])/npos
      output  = ("## %-30s\t1.0000\t") % ("NO Gaps Left Boundary")
      output += ("pos\t%d\t%%alig\t%.4f") % (boundaries[2], ratio)
      ratio = float(boundaries[5])/npos
      output += ("\n## %-30s\t1.0000\t") % ("NO Gaps Right Boundary")
      output += ("pos\t%d\t%%alig\t%.4f") % (boundaries[5], ratio)
    else:
      output = ("%d,%d") % (boundaries[2], boundaries[5])

  elif not output and boundaries[0] != boundaries[3]:

    ## If columns with no gaps are the first/last ones found - select them as
    ## the boundaries independently of user input parameters.
    left = boundaries[0]
    left_score = boundaries[1]
    if boundaries[2] != -1 and boundaries[2] < boundaries[0]:
      left = boundaries[2]
      left_score = 1.0

    right = boundaries[3]
    right_score = boundaries[4]
    if boundaries[5] != -1 and boundaries[5] > boundaries[3]:
      right = boundaries[5]
      right_score = 1.0

    if not args.oneLine:
      ratio_l = float(left)/npos
      ratio_r = float(right)/npos
      
      output =  ("## %-30s\t") % ("Best Gaps_Score Left Boundary")
      output += ("%.4f\tpos\t%d\t%%alig\t%.4f\n") % (left_score, left, ratio_l)
      output += ("## %-30s\t") % ("Best Gaps_Score Right Boundary")
      output += ("%.4f\tpos\t%d\t%%alig\t%.4f") % (right_score, right, ratio_r)
    else:
      output = ("%d,%d") % (left, right)

  ## If there is no output, and the user has set-up "--get_best_boundaries"
  elif not output and args.bestBoundaries:
    left = putatitve[0]
    left_score = putative[1]

    right = putative[3]
    right_score = putative[4]

    if not args.oneLine:
      ratio_l = float(left)/npos
      ratio_r = float(right)/npos
      
      output =  ("## %-30s\t") % ("Best_found Gaps_Score Left Boundary")
      output += ("%.4f\tpos\t%d\t%%alig\t%.4f\n") % (left_score, left, ratio_l)
      output += ("## %-30s\t") % ("Best_found Gaps_Score Right Boundary")
      output += ("%.4f\tpos\t%d\t%%alig\t%.4f") % (right_score, right, ratio_r)
    else:
      output = ("%d,%d") % (left, right)

  ## Generate a warning for those cases where no boundaries have been found
  if not output:
    output = "WARNING: OUTPUT NOT AVAILABLE"
  print output
### ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ****
if __name__ == "__main__":
  sys.exit(main())
