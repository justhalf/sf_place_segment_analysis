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

def print_stats(sfs, docs, ignore_doc_no_sf=False, span_to_entity_id={}, entities={}, mention_selection='closest',
                outfile=sys.stdout, outpath=''):
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
                loc_seg_nums = [get_segment(doc, start, end)]
            for loc_seg_num in loc_seg_nums:
                sf_to_loc.append((seg_num, loc_seg_num, len(doc.segments)))
    print('Total SFs: {}'.format(len(sfs)))
    print('SFs with segment ID: {}'.format(len(sfs) - sf_no_segment_count))
    print('SFs with place: {}'.format(sf_with_place))
    diff_counts = {}
    total_diffs = 0
    for seg_num, loc_seg_num, num_segs in sf_to_loc:
        print('{},{},{}'.format(seg_num, loc_seg_num, num_segs), file=outfile)
        diff = abs(seg_num - loc_seg_num)
        if diff not in diff_counts:
            diff_counts[diff] = 0
        diff_counts[diff] += 1
        total_diffs += 1

    figpath, ext = os.path.splitext(outpath)
    figpath = '{}.pdf'.format(figpath)
    plt.figure()
    plt.plot(seg_num, loc_seg_num)
    plt.ylabel('Segment ID of the Place')
    plt.xlabel('Segment ID of the SF description')
    plt.savefig(figpath)
    for key, count in sorted(diff_counts.items()):
        print('{}: {:.2f}%'.format(key, 100.0*count/total_diffs))

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
    else:
        raise ValueError('Either --json_in or --sf_anno must be present')

    if args.out_file:
        with open(args.out_file, 'w') as outfile:
            print_stats(sfs, docs, args.ignore_doc_no_sf, span_to_entity_id=span_to_entity_id,
                        mention_selection=args.mention_selection, entities=entities, outfile=outfile,
                        outpath=args.out_file)
    else:
        print_stats(sfs, docs, args.ignore_doc_no_sf, span_to_entity_id=span_to_entity_id,
                    mention_selection=args.mention_selection, entities=entities, outfile=outfile,
                    outpath=args.out_file)

if __name__ == '__main__':
    main()

