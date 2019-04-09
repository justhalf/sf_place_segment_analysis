# -*- coding: utf-8 -*-
"""
12 Mar 2018
To get location statistics
"""

# Import statements
from __future__ import print_function, division
import sys
import os
from lor_utils import read_ltf_files, read_sf_annos, SituationFrame as SF
from lor_utils import read_sf_mentions_dir
from collections import defaultdict
from pprint import pprint
from argparse import ArgumentParser
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math

def add_value_labels(ax, spacing=3):
    """Add labels to the end of each bar in a bar chart.

    Taken from https://stackoverflow.com/questions/28931224/adding-value-labels-on-a-matplotlib-bar-chart

    Arguments:
        ax (matplotlib.axes.Axes): The matplotlib object containing the axes
            of the plot to annotate.
        spacing (int): The distance between the labels and the bars.
    """

    (y_bottom, y_top) = ax.get_ylim()
    y_height = y_top - y_bottom
    # For each bar: Place a label
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2

        # Number of points between bar and label. Change to your liking.
        space = spacing
        # if y_value / y_height > 0.95:
        #     space = -1.25*space
        # Vertical alignment for positive values
        va = 'bottom'

        # If value of bar is negative: Place label below bar
        if y_value < 0:
            # Invert space to place label below
            space *= -1
            # Vertically align label at top
            va = 'top'

        # Use Y value as label and format number with one decimal place
        label = "{:.2f}".format(y_value)

        # Create annotation
        ax.annotate(
            label,                      # Use `label` as label
            (x_value, y_value),         # Place label at end of the bar
            xytext=(0, space),          # Vertically shift label by `space`
            textcoords="offset points", # Interpret `xytext` as offset in points
            ha='center',                # Horizontally center label
            va=va,                      # Vertically align label differently for
                                        # positive and negative values.
            fontsize=5)

def print_stats(sfs, docs, ignore_doc_no_sf=False, span_to_entity_id={}, entities={}, mention_selection='closest',
                outfile=sys.stdout, outpath='', lang=''):
    if len(sfs) > 0 and not isinstance(sfs[0], SF):
        sfs = [SF.from_dict(sf) for sf in sfs]
    docs_by_ids = docs
    docs = list(docs.values())
    def get_segment(doc, start, end):
        """Returns the segment ID in the specified document containing the offsets start to end"""
        for segment in doc.segments:
            if segment.span.start <= start and segment.span.end >= end:
                return segment

    sf_to_loc = []
    sf_no_segment_count = 0
    sf_with_place = 0
    for sf in sfs:
        if not sf.seg_id:
            # No segment ID information for this SF is found (i.e., the description field is empty or not part of the 
            # actual document)
            sf_no_segment_count += 1
            continue
        seg_num = int(sf.seg_id.split('-')[1])
        doc_id = sf.doc_id
        doc = docs_by_ids[doc_id]
        if sf.place_mention:
            sf_with_place += 1
            place_mention = sf.place_mention
            start, end = place_mention.span.start, place_mention.span.end
            span = (start, end)
            # Get the corresponding entity (collection of mentions)
            if span in span_to_entity_id:
                ent_id = span_to_entity_id[span]
            else:
                ent_id = None
            # This list represents the list of segment IDs (might be repeated) containing the place mention
            loc_seg_nums = [10000]
            if mention_selection == 'closest':
                for mention in entities[ent_id]:
                    try:
                        # Cache of mention segment ID
                        loc_seg_num = mention.seg_id
                    except:
                        # First time seeing this mention: calculate the segment ID and cache
                        men_start, men_end = mention.span.start, mention.span.end
                        segment = get_segment(doc, men_start, men_end)
                        if not segment:
                            continue
                        loc_seg_num = int(segment.seg_id.split('-')[1])
                        mention.seg_id = loc_seg_num
                    if abs(seg_num - loc_seg_num) < abs(seg_num - loc_seg_nums[0]):
                        loc_seg_nums = [loc_seg_num]
                    elif abs(seg_num - loc_seg_num) == abs(seg_num - loc_seg_nums[0]):
                        loc_seg_nums.append(loc_seg_num)
            else: # mention_selection == 'original'
                segment = get_segment(doc, start, end)
                if not segment:
                    continue
                loc_seg_num = int(segment.seg_id.split('-')[1])
                loc_seg_nums = [loc_seg_num]
            for loc_seg_num in loc_seg_nums:
                sf_to_loc.append((doc_id, seg_num, loc_seg_num, len(doc.segments)))
    print('Total SFs: {}'.format(len(sfs)))
    print('SFs with segment ID: {}'.format(len(sfs) - sf_no_segment_count))
    print('SFs with place: {}'.format(sf_with_place))
    diff_counts = {}
    total_diffs = 0
    seg_loc_tup_count = {}
    for doc_id, seg_num, loc_seg_num, num_segs in sf_to_loc:
        print('{},{},{},{}'.format(doc_id, seg_num, loc_seg_num, num_segs), file=outfile)
        diff = abs(seg_num - loc_seg_num)
        if diff not in diff_counts:
            diff_counts[diff] = 0
        diff_counts[diff] += 1
        total_diffs += 1
        tup = (seg_num, loc_seg_num)
        if tup not in seg_loc_tup_count:
            seg_loc_tup_count[tup] = 0
        seg_loc_tup_count[tup] += 1
    tups, counts = zip(*seg_loc_tup_count.items())
    seg_nums, loc_seg_nums = zip(*tups)
    # Currently not used, to visualize how many data points per dot in the scatter plot
    counts = [math.log(count) for count in counts]

    # Plot SF vs Place
    figpath, ext = os.path.splitext(outpath)
    scatter_figpath = '{}.png'.format(figpath)
    plt.figure(figsize=(5,5))
    max_val = max([max(seg_nums), max(loc_seg_nums)])
    max_val = max(max_val, 40)
    plt.plot([-0.5, max_val+0.5], [-0.5, max_val+0.5], color='black', zorder=-1, alpha=0.5)
    plt.scatter(seg_nums, loc_seg_nums)
    # plt.scatter(seg_nums, loc_seg_nums, c=counts)
    plt.ylabel('Segment ID of the Place')
    plt.xlabel('Segment ID of the SF description')
    plt.title('SF trigger vs SF Place location ({})'.format(lang))
    plt.tight_layout()
    plt.savefig(scatter_figpath)

    # Plot histogram of distance
    hist_figpath = '{}_hist.png'.format(figpath)
    dists, dist_counts = [], []
    for dist, count in sorted(diff_counts.items()):
        print('{}: {:.2f}%'.format(dist, 100.0*count/total_diffs))
        dists.append(dist)
        dist_counts.append(1.0*count/total_diffs)
    fig = plt.figure(figsize=(6,4))
    plt.bar(dists, dist_counts)
    plt.ylabel('Ratio of Frequency')
    plt.xlabel('Distance between SF description and SF Place')
    plt.title('Distribution of segment distances ({})'.format(lang))
    plt.tight_layout()
    ax = fig.axes[0]
    add_value_labels(ax)
    plt.savefig(hist_figpath)

def create_span_to_entity_id(entities):
    result = {}
    for entity_id, mentions in entities.items():
        for mention in mentions:
            span = (mention.span.start, mention.span.end)
            result[span] = entity_id
    return result

def main():
    parser = ArgumentParser(description='Print statistics of a list of SFs')
    # Input paths
    parser.add_argument('--ltf_dir', help='The LTF directory of documents')
    parser.add_argument('--mention_dir', help='The gold entity annotations per document')

    # Either one of the following options must be present
    parser.add_argument('--json_in', help='The input JSON file of SFs')
    parser.add_argument('--sf_anno', help='The directory containing SFs')

    # Output path
    parser.add_argument('--out_file', help='The output file. Default to stdout')

    # Extra arguments
    parser.add_argument('--ignore_doc_no_sf', action='store_true', help='To ignore documents without SFs')
    parser.add_argument('--mention_selection', choices=['original', 'closest'], default='closest',
                        help='How to select the mention associated with the SF Place when there are multiple mentions')
    parser.add_argument('--lang',
                        help='The language code')
    args = parser.parse_args()

    docs = read_ltf_files(args.ltf_dir, progress_bar=False, outtype='dict')
    # Entities will be a dictionary from entity ID (Ent-IL6_NW_020556_20151229_H0040MWIE-113)
    # into list of mentions (Entity object from lor_utils)
    # Attributes: doc_id, ent_id, men_id, ent_type, men_status, span, men_text
    entities = read_sf_mentions_dir(args.mention_dir, outtype='dict')
    span_to_entity_id = create_span_to_entity_id(entities)
    if args.json_in:
        with open(args.json_in, 'r') as infile:
            sfs = json.load(infile)
    elif args.sf_anno:
        sfs = read_sf_annos(args.sf_anno)
        for sf in sfs:
            doc_id = sf.doc_id
            doc = docs.get(doc_id, None)
            if not doc:
                continue
            if sf.text is not None and sf.text != 'none':
                for segment in doc.segments:
                    if sf.text in segment.text:
                        sf.seg_id = segment.seg_id
                        break
    else:
        raise ValueError('Either --json_in or --sf_anno must be present')

    if args.out_file:
        with open(args.out_file, 'w') as outfile:
            print_stats(sfs, docs, args.ignore_doc_no_sf, span_to_entity_id=span_to_entity_id,
                        mention_selection=args.mention_selection, entities=entities, outfile=outfile,
                        outpath=args.out_file, lang=args.lang)
    else:
        print_stats(sfs, docs, args.ignore_doc_no_sf, span_to_entity_id=span_to_entity_id,
                    mention_selection=args.mention_selection, entities=entities, outfile=outfile,
                    outpath=args.out_file, lang=args.lang)

if __name__ == '__main__':
    main()

