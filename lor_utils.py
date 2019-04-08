# -*- coding: utf-8 -*-
"""
13 Oct 2017
Collection of utility functions for Lorelei project
"""

# Import statements
from __future__ import print_function
import sys
import codecs
from bs4 import BeautifulSoup as BS
import os
from collections import OrderedDict
from tqdm import tqdm
from multiprocessing import Pool
from six import string_types
from copy import copy, deepcopy
import signal
from functools import partial
from unidecode import unidecode
import time
from datetime import datetime
from multiprocessing.managers import BaseManager
import re
import numpy as np

class KBEntry(object):
    def __init__(self, origin, entity_type, entityid, name, asciiname, latitude, longitude, feature_class=None, 
            feature_class_name=None, feature_code=None, feature_code_name=None, feature_code_description=None, country_code=None, 
            country_code_name=None, cc2=None, admin1_code=None, admin1_code_name=None, admin2_code=None, admin2_code_name=None, admin3_code=None,
            admin4_code=None, population=None, elevation=None, dem=None, timezone=None, modification_date=None, per_gpe_loc_of_association=None, 
            per_title_or_position=None, per_org_of_association=None, per_role_in_incident=None, per_year_of_birth=None, per_year_of_death=None,
            per_gender=None, per_family_member=None, note=None, aim=None, org_date_established=None, date_established_note=None, org_website=None, 
            org_gpe_loc_of_association=None, org_members_employees_per=None, org_parent_org=None, executive_board_members=None, 
            jurisdiction=None, trusteeship_council=None, national_societies=None, external_link=None, brief=False):
        self.origin = origin
        self.entity_type = entity_type
        self.entityid = entityid
        self.name = name
        self.asciiname = asciiname
        try:
            self.latitude = float(latitude)
        except:
            self.latitude = None
        try:
            self.longitude = float(longitude)
        except:
            self.longitude = None
        if brief:
            return
        self.feature_class = feature_class
        self.feature_class_name = feature_class_name
        self.feature_code = feature_code
        self.feature_code_name = feature_code_name
        self.feature_code_description = feature_code_description
        self.country_code = country_code
        self.country_code_name = country_code_name
        self.cc2 = cc2
        self.admin1_code = admin1_code
        self.admin1_code_name = admin1_code_name
        self.admin2_code = admin2_code
        self.admin2_code_name = admin2_code_name
        self.admin3_code = admin3_code
        self.admin4_code = admin4_code
        self.population = population
        try:
            self.elevation = float(elevation)
        except:
            self.elevation = elevation
        self.dem = dem
        self.timezone = timezone
        self.modification_date = modification_date
        self.per_gpe_loc_of_association = per_gpe_loc_of_association
        self.per_title_or_position = per_title_or_position
        self.per_org_of_association = per_org_of_association
        self.per_role_in_incident = per_role_in_incident
        self.per_year_of_birth = per_year_of_birth
        self.per_year_of_death = per_year_of_death
        self.per_gender = per_gender
        self.per_family_member = per_family_member
        self.note = note
        self.aim = aim
        self.org_date_established = org_date_established
        self.date_established_note = date_established_note
        self.org_website = org_website
        self.org_gpe_loc_of_association = org_gpe_loc_of_association
        self.org_members_employees_per = org_members_employees_per
        self.org_parent_org = org_parent_org
        self.executive_board_members = executive_board_members
        self.jurisdiction = jurisdiction
        self.trusteeship_council = trusteeship_council
        self.national_societies = national_societies
        self.external_link = external_link


class KBManager(BaseManager): pass
KBManager.register('KB')

class KBDict(object):
    def __init__(self, kb):
        self.kb = kb

    def __len__(self):
        return self.kb.len()

    def __getitem__(self, key):
        return self.kb.getitem(key)
    
    def __contains__(self, key):
        return self.kb.haskey(key)

    def __setitem__(self, key, value):
        raise ValueError('KB from Manager is read-only.')

    def get(self, key, default=KBEntry('', '', '', '', '', 0.0, 0.0)):
        return self.kb.getitem(key, default)


def get_kb_from_manager(port=50000):
    """To get KB from KB manager, this saves loading time

    Needs KB manager to be running at the specified port
    """
    m = KBManager(address=('', port), authkey='ariel'.encode('utf-8'))
    try:
        m.connect()
    except ConnectionRefusedError:
        raise OSError('Cannot connect to KB manager at port {}'.format(port))
    kb = m.KB()
    kb = KBDict(kb)
    return kb


class Version(object):
    """An enum representing different versions of format
    """
    v2017 = 'v2017'
    v2018 = 'v2018'
    v2018_dry = 'v2018_dry'
    vMacedonianEx = 'vMacedonianEx'


_SF_TYPES = ['terrorism', 'crimeviolence', 'regimechange', 'food', 'water', 'med', 'infra', 'shelter', 'evac', 'utils', 'search']
SF_TYPES = {
            Version.v2017: _SF_TYPES,
            Version.v2018: _SF_TYPES,
            Version.v2018_dry: _SF_TYPES,
            Version.vMacedonianEx: _SF_TYPES
            }

class Span(object):
    """An object storing a start and end offsets (both inclusive)
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end
    
    def contains(self, span):
        return self.start <= span.start and self.end >= span.end

    def __eq__(self, span):
        if not isinstance(span, self.__class__):
            return NotImplemented
        return self.start == span.start and self.end == span.end

    def __ne__(self, span):
        if not isinstance(span, self.__class__):
            return NotImplemented
        return not (self == span)

    def hash(self):
        return hash((self.start, self.end))

    def __iter__(self):
        return iter((self.start, self.end))

    def __getitem__(self, i):
        return (self.start, self.end)[i]

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def to_dict(self):
        result = OrderedDict()
        result['start'] = self.start
        result['end'] = self.end
        return result

    to_complete_dict = to_dict
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__

class Token(object):
    def __init__(self, tok_id, pos, morph, span, text):
        self.tok_id = tok_id
        self.pos = pos
        self.morph = morph
        self.span = span
        self.text = text
        self.text_transliterated = None

    def __repr__(self):
        return self.text
    
    __str__ = __repr__

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def to_dict(self):
        result = OrderedDict()
        result['tok_id'] = self.tok_id
        result['pos'] = self.pos
        result['morph'] = self.morph
        result['span'] = self.span.to_dict()
        result['text'] = self.text
        if self.text_transliterated is not None:
            result['text_transliterated'] = self.text_transliterated
        return result

    to_complete_dict = to_dict

    def transliterate(self, f=unidecode):
        self.text_transliterated = f(self.text)

class Segment(object):
    """An object storing a segment, which is a sequence of string tokens
    """
    def __init__(self, seg_id, text, span, tokens, token_spans, src_file=''):
        self.seg_id = seg_id
        self.text = text
        self.span = span
        self.tokens = tokens
        self.token_spans = token_spans
        self.src_file = src_file
        try:
            self.doc_id = os.path.splitext(os.path.basename(os.path.normpath(src_file)))[0]
        except:
            self.doc_id = ''
        self.text_transliterated = None
    
    def __len__(self):
        return len(self.tokens)

    def __iter__(self):
        return iter(self.tokens)
    
    def __getitem__(self, i):
        return self.tokens[i]

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def to_dict(self):
        result = OrderedDict()
        result['doc_id'] = self.doc_id
        result['seg_id'] = self.seg_id
        result['text'] = self.text
        result['span'] = self.span.to_dict()
        result['tokens'] = [token.to_dict() for token in self.tokens]
        result['src_file'] = self.src_file
        if self.text_transliterated is not None:
            result['text_transliterated'] = self.text_transliterated
        return result

    to_complete_dict = to_dict

    def transliterate(self, f=unidecode):
        self.text_transliterated = f(self.text)
        for token in self.tokens:
            token.transliterate(f)
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__

class Document(object):
    """An object storing a document, which is a list of segments
    """
    def __init__(self, doc_id, lang, tokenization, grammar, raw_text_len, raw_text_md5, segments):
        self.doc_id = doc_id
        self.lang = lang
        self.tokenization = tokenization
        self.grammar = grammar
        self.raw_text_len = raw_text_len
        self.raw_text_md5 = raw_text_md5
        self.segments = segments
        self.text = None
        self.text_transliterated = None

    def get_text(self, start=None, end=None, span=None):
        text = ''
        last_end = 0
        if span:
            start = span.start
            end = span.end+1
        for segment in self.segments:
            seg_start, seg_end = segment.span
            text += ' '*(seg_start-last_end)
            text += segment.text
            last_end = seg_end+1
        if start is not None and end is not None:
            return text[start:end]
        return text

    def get_segment(self, seg_id):
        try:
            return self.segments[int(seg_id.split('-')[1])]
        except:
            return None

    def __len__(self):
        return len(self.segments)

    def __iter__(self):
        return iter(self.segments)

    def __getitem__(self, i):
        return self.segments[i]

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def to_dict(self):
        result = OrderedDict()
        result['doc_id'] = self.doc_id
        result['lang'] = self.lang
        result['tokenization'] = self.tokenization
        result['grammar'] = self.grammar
        result['raw_text_len'] = self.raw_text_len
        result['raw_text_md5'] = self.raw_text_md5
        result['segments'] = [segment.to_dict() for segment in self.segments]
        if self.text_transliterated is not None:
            result['text_transliterated'] = self.text_transliterated
        return result

    to_complete_dict = to_dict

    def transliterate(self, f=unidecode):
        if self.text is not None:
            self.text_transliterated = f(self.text)
        for segment in self.segments:
            segment.transliterate(f)
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__

class Alignment(object):
    """Alignment information between two Documents
    
    alignments should be a list of tuples, each tuple representing corresponding mapping between segments in the source
    document and segments in the translation document, each element of the tuple is a list of segments.
    For example:
    [(['segment-0'], ['segment-0']),
     (['segment-1', 'segment-2'], ['segment-1']),
     (['segment-3'], ['segment-2', 'segment-3'])]
    """
    def __init__(self, source_id, translation_id, alignments):
        self.source_id = source_id
        self.translation_id = translation_id
        self.alignments = alignments
        self.source_mapping = {}
        self.translation_mapping = {}
        for alignment in alignments:
            source_seg_ids, translation_seg_ids = alignment
            for source_seg_id in source_seg_ids:
                self.source_mapping[source_seg_id] = alignment
            for translation_seg_id in translation_seg_ids:
                self.translation_mapping[translation_seg_id] = alignment

    def map_source(self, source_seg_id):
        return self.source_mapping.get(source_seg_id, ([source_seg_id],[]))

    def map_translation(self, translation_seg_id):
        return self.translation_mapping.get(translation_seg_id, ([translation_seg_id],[]))

class Entity(object):
    """An object storing an entity (usually from sf_anno/mentions), representing NER output (no kb_id)
    """
    def __init__(self, doc_id, ent_id, men_id, ent_type, men_status, span, men_text):
        self.doc_id = doc_id
        self.ent_id = ent_id
        self.men_id = men_id
        self.ent_type = ent_type
        self.men_status = men_status
        self.span = span
        self.men_text = men_text

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def to_dict(self):
        result = OrderedDict()
        result['Start'] = self.span.start
        result['EntityType'] = self.ent_type
        result['End'] = self.span.end
        result['Place'] = self.men_text
        if hasattr(self, 'men_text_kb'):
            result['KB_Place'] = self.men_text_kb
        return result

    def to_complete_dict(self):
        result = OrderedDict()
        result['doc_id'] = self.doc_id
        result['ent_id'] = self.ent_id
        result['men_id'] = self.men_id
        result['ent_type'] = self.ent_type
        result['men_status'] = self.men_status
        result['span'] = self.span.to_dict()
        result['men_text'] = self.men_text
        return result
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__

class Mention(object):
    """An object storing a mention (usually from il*_edl.tab file)
    """
    def __init__(self, sys_id, doc_id, men_id, men_text, span, kb_id, ent_type, men_type, conf, men_text_kb=None):
        self.sys_id = sys_id
        self.doc_id = doc_id
        self.men_id = men_id
        self.men_text = men_text
        self.span = span
        self.kb_id = kb_id
        self.ent_type = ent_type
        self.men_type = men_type
        self.conf = conf
        self.men_text_kb = men_text_kb

    def to_dict(self):
        result = OrderedDict()
        result['Start'] = self.span.start
        result['EntityType'] = self.ent_type
        result['End'] = self.span.end
        result['Place'] = self.men_text
        result['KB_ID'] = self.kb_id
        result['KB_Place'] = self.men_text_kb
        return result

    def to_complete_dict(self):
        result = OrderedDict()
        result['sys_id'] = self.sys_id
        result['doc_id'] = self.doc_id
        result['men_id'] = self.men_id
        result['men_text'] = self.men_text
        result['men_text_kb'] = self.men_text_kb
        result['span'] = self.span.to_complete_dict()
        result['kb_id'] = self.kb_id
        result['ent_type'] = self.ent_type
        result['men_type'] = self.men_type
        result['conf'] = self.conf
        return result

    @classmethod
    def from_dict(cls, place_mention, documents, mentions_by_doc_and_seg, doc_id, seg_id=None):
        if not place_mention:
            return None
        start = place_mention.get('Start', -1)
        end = place_mention.get('End', -1)
        ent_type = place_mention.get('EntityType', None)
        text = place_mention.get('Place', None)
        kb_id = place_mention.get('KB_ID', None)
        kb_text = place_mention.get('KB_Place', None)
        span = Span(start, end)
        if seg_id is None:
            if doc_id in documents:
                doc = documents[doc_id]
                for segment in doc.segments:
                    seg_id = segment.seg_id
                    if not segment.span.contains(span):
                        continue
                    key = (doc_id, seg_id)
                    for mention in mentions_by_doc_and_seg.get(key, []):
                        if mention.span == span:
                            return mention
        else:
            for cur_seg_id in seg_id.split('\t'):
                key = (doc_id, cur_seg_id)
                for mention in mentions_by_doc_and_seg.get(key, []):
                    if mention.span == span:
                        return mention
        result = Mention(None, None, None, None, None, None, None, None, None)
        result.doc_id = doc_id
        result.span = span
        result.men_id = '{}:{}-{}'.format(doc_id, span.start, span.end)
        result.men_text = text
        result.ent_type = ent_type
        result.kb_id = kb_id
        result.men_text_kb = kb_text
        return result

    @classmethod
    def from_text(cls, place_mention, documents, mentions_by_doc_and_seg, doc_id, seg_id=None):
        text = place_mention
        if doc_id in documents:
            doc = documents[doc_id]
            for segment in doc.segments:
                seg_id = segment.seg_id
                key = (doc_id, seg_id)
                for mention in mentions_by_doc_and_seg.get(key, []):
                    if mention.men_text == text:
                        return mention
        # The case where the mention text is not found in the document
        result = Mention(None, None, None, None, None, None, None, None, None)
        result.doc_id = doc_id
        result.men_text = text
        return result
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

class Keyword(object):
    def __init__(self, text, span, weight, source_keyword):
        self.text = text
        self.span = span
        self.weight = weight
        self.source_keyword = source_keyword

    def to_dict(self):
        result = OrderedDict()
        result['source_keyword'] = self.source_keyword
        result['start_char'] = self.span.start if self.span is not None else -1
        result['text'] = self.text
        result['end_char'] = self.span.end if self.span is not None else -1
        result['weight'] = self.weight
        return result

    to_complete_dict = to_dict

    @classmethod
    def from_dict(self, keyword):
        result = Keyword(None, None, None, None)
        result.text = keyword['text']
        result.span = Span(int(keyword['start_char']), int(keyword['end_char']))
        result.weight = keyword['weight']
        result.source_keyword = keyword['source_keyword']
        return result

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__

class Status(object):
    @classmethod
    def from_dict(cls, status):
        if 'Need' in status:
            return StatusNeed.from_dict(status)
        elif 'Issue' in status:
            return StatusIssue.from_dict(status)
        else:
            raise ValueError('Not a status dict: {}'.format(status))

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__

class StatusNeed(object):
    def __init__(self, need_status='current', relief_status='insufficient', urgent_status=True):
        if need_status is None:
            need_status = 'current'
        if relief_status is None:
            relief_status = 'insufficient'
        if urgent_status is None:
            urgent_status=True
        self.need_status = need_status
        self.relief_status = relief_status
        self.urgent_status = urgent_status

    def to_dict(self):
        result = OrderedDict()
        result['Need'] = self.need_status
        result['Urgent'] = self.urgent_status
        result['Relief'] = self.relief_status
        return result

    def to_complete_dict(self):
        result = OrderedDict()
        result['need_status'] = self.need_status
        result['relief_status'] = self.relief_status
        result['urgent_status'] = self.urgent_status
        return result

    @classmethod
    def from_dict(cls, status):
        result = StatusNeed()
        result.need_status = status['Need']
        if 'Urgent' in status:
            result.urgent_status = status['Urgent'] not in ['false', 'False', False]
        if 'Relief' in status:
            result.relief_status = status['Relief']
        return result

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

class StatusIssue(object):
    def __init__(self, issue_status='current', urgent_status=True):
        if issue_status is None:
            issue_status = 'current'
        self.issue_status = issue_status
        self.urgent_status = urgent_status

    def to_dict(self):
        result = OrderedDict()
        result['Issue'] = self.issue_status
        result['Urgent'] = self.urgent_status
        return result

    def to_complete_dict(self):
        result = OrderedDict()
        result['issue_status'] = self.issue_status
        result['urgent_status'] = self.urgent_status
        return result

    @classmethod
    def from_dict(cls, status):
        result = StatusIssue()
        result.issue_status = status['Issue']
        if 'Urgent' in status:
            result.urgent_status = status['Urgent'] not in ['false', 'False', False]
        return result

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

class SituationFrame(object):
    warnings = {}
    """An object storing a situation frame (from sf_anno/issues and sf_anno/needs)

    Use the function sf.is_need or sf.is_issue to determine whether this SF is a need or an issue
    """
    def __init__(self, user_id, doc_id, frame_id, frame_type, place_id, proxy_status, need_type=None, need_status=None, issue_type=None, issue_status=None, urgency_status=None, resolution_status=None, reported_by=None, resolved_by=None, description=None, place=None, scope=None, severity=None, kb_id=None, documents={}):
        self.user_id = user_id
        self.doc_id = doc_id
        self.frame_id = frame_id
        self.frame_type = frame_type
        self.place_id = place_id
        self.proxy_status = proxy_status
        self.need_type = need_type
        self.need_status = need_status
        self.issue_type = issue_type
        self.issue_status = issue_status
        self.urgency_status = urgency_status
        self.resolution_status = resolution_status
        self.reported_by = reported_by
        self.resolved_by = resolved_by
        self.description = description
        self._scope = scope
        self._severity = severity
        self.kb_id = kb_id
        """The KBEntry associated to the location of this SF"""
        self.place = place

        # For system output
        if self.is_issue():
            self._type = self.issue_type
        elif self.is_need():
            self._type = self.need_type
        else:
            self._type = None

        """Calculate urgency_status from scope and severity"""
        self.update_urgency()
        self.seg_id = None
        if self.seg_id is None and self.description is not None and documents is not None:
            self.infer_seg_id_from_description(documents)
        self.source = self.user_id
        self.type_confidence = 1.0
        if self.description is not None and self.description != 'none':
            self.text = self.description
        else:
            self.text = None
        self.keywords = None
        if self.is_need():
            if self.urgency_status is not None:
                self.status = StatusNeed(self.need_status, self.resolution_status, self.urgency_status)
            else:
                self.status = StatusNeed(self.need_status, self.resolution_status)
        elif self.is_issue():
            if self.urgency_status is not None:
                self.status = StatusIssue(self.issue_status, urgent_status=self.urgency_status)
            else:
                self.status = StatusIssue(self.issue_status)
        else:
            self.status = None
        if self.place is not None:
            """The Entity (from NER) or Mention (from EDL) object associated with this SF"""
            self.place_mention = Mention(user_id, doc_id, '{}_{}'.format(frame_id, place_id), place.name, Span(-1, -1), place.entityid, place.entity_type, None, 1.0)
        else:
            self.place_mention = None

    def infer_seg_id_from_description(self, documents):
        if self.doc_id not in documents:
            return False
        doc = documents[self.doc_id]
        for segment in doc:
            if self.description in segment.text:
                self.seg_id = segment.seg_id
                return True
        return False

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value in ['crimeviolence', 'terrorism', 'regimechange']:
            self.frame_type = 'issue'
            self.issue_type = value
            self.need_type = None
            if isinstance(self.status, StatusNeed):
                self.status = StatusIssue(self.status.need_status, urgent_status=self.status.urgent_status)
        else:
            self.frame_type = 'need'
            self.issue_type = None
            self.need_type = value
            if isinstance(self.status, StatusIssue):
                self.status = StatusNeed(self.status.issue_status, urgent_status=self.status.urgent_status)
        self._type = value

    @property
    def scope(self):
        return self._scope

    @scope.setter
    def scope(self, value):
        self._scope = value
        self.update_urgency()

    @property
    def severity(self):
        return self._severity
    
    @severity.setter
    def severity(self, value):
        self._severity = value
        self.update_urgency()

    def update_urgency(self):
        """ (from NIST LoReHLT 2018 Evaluation Plan 1.0.4, section 16.2.1)
        Scope can be of “Individual/ Small Group”, “Large Group”, “Municipality”, “Multiple Municipalities”; severity
        can be of “Inconvenience/Discomfort”, “Non-life Threatening Injury or Destruction”, “Possible Loss of Life”,
        “Certain Loss of Life”. Since the SF participants continue this year to label “Urgent” frames with a binary
        label, the “Scope” and “Severity” annotations are combined and converted to the single binary value for
        scoring purposes as follows: if a situation frame is of at least the scope of a “Large Group”, or severity of
        at least “Non-life Threatening Injury or Destruction”, the frame will be considered urgent.
        """
        urgency = self.get_urgency(self._scope, self._severity)
        if urgency is not None:
            self.urgency_status = urgency

    @staticmethod
    def get_urgency(scope, severity):
        if scope is None or severity is None:
            # Do not update if there is no scope or severity information
            return
        scope_significant = False
        if scope != 'none' and int(scope.split('_')[0]) > 1:
            scope_significant = True
        severity_significant = False
        if severity != 'none' and int(severity.split('_')[0]) > 1:
            severity_significant = True
        return (scope_significant and severity_significant)

    def is_grave(self):
        return (self.is_need() and
                self.status is not None and
                self.status.need_status == 'current' and
                self.status.urgent_status and
                self.status.relief_status == 'insufficient')

    def has_place_id(self):
        return self.place_id is not None and self.place_id != 'none'

    def is_need(self):
        return self.frame_type == 'need'

    def is_issue(self):
        return self.frame_type == 'issue'

    def to_complete_dict(self, entities=None, documents={}):
        result = OrderedDict()
        result['user_id'] = self.user_id
        result['doc_id'] = self.doc_id
        result['frame_id'] = self.frame_id
        result['frame_type'] = self.frame_type
        result['place_id'] = self.place_id
        result['place'] = self.place 
        result['proxy_status'] = self.proxy_status
        result['need_type'] = self.need_type
        result['need_status'] = self.need_status
        result['issue_type'] = self.issue_type
        result['issue_status'] = self.issue_status
        result['urgency_status'] = self.urgency_status
        result['resolution_status'] = self.resolution_status
        result['reported_by'] = self.reported_by
        result['resolved_by'] = self.resolved_by
        result['description'] = self.description
        result['type'] = self.type
        if self.seg_id is None and self.description is not None and documents is not None:
            self.infer_seg_id_from_description(documents)
        result['seg_id'] = self.seg_id
        result['source'] = self.source
        result['type_confidence'] = self.type_confidence
        result['text'] = self.text
        if self.keywords is not None:
            result['keywords'] = [keyword.to_complete_dict() for keyword in self.keywords]
        result['status'] = self.status if (self.status is None or type(self.status) is str) else self.status.to_complete_dict()
        if self.place_mention is None and self.has_place_id() and entities is not None:
            self.assign_place_mention(entities)
        result['place_mention'] = None if self.place_mention is None else self.place_mention.to_complete_dict()
        result['scope'] = self.scope
        result['severity'] = self.severity
        result['kb_id'] = self.kb_id
        return result

    def to_dict(self, entities=None, version=Version.v2017):
        result = OrderedDict()
        result['DocumentID'] = self.doc_id
        result['Type'] = self.type
        if version == Version.v2017:
            result['TypeConfidence'] = self.type_confidence
        else:
            result['Confidence'] = self.type_confidence
        result['Text'] = self.text
        if (self.place_mention is None and self.has_place_id() and entities is not None):
            self.assign_place_mention(entities)
        if self.place_mention is not None:
            result['PlaceMention'] = self.place_mention.to_dict()
        else:
            result['PlaceMention'] = {}
        # if version in [Version.v2018, Version.v2018_dry]:
        if self.kb_id is not None:
            result['Place_KB_ID'] = self.kb_id
        elif self.place is not None:
            result['Place_KB_ID'] = self.place.entityid
        elif self.place_mention is not None:
            if hasattr(self.place_mention, 'kb_id'):
                # Mention from predictions
                result['Place_KB_ID'] = self.place_mention.kb_id
            else:
                # Mention from gold file
                result['Place_KB_ID'] = self.place_mention.ent_id
        else:
            result['Place_KB_ID'] = ''
        if result['Place_KB_ID'] is None:
            result['Place_KB_ID'] = ''
        result['SegmentID'] = self.seg_id
        result['Source'] = self.source
        if version in [Version.v2018_dry]:
            result['Justification'] = self.seg_id
        if version in [Version.v2018, Version.vMacedonianEx]:
            try:
                result['Justification_ID'] = self.seg_id.split('\t')[0]
            except:
                result['Justification_ID'] = self.seg_id
        if version in [Version.vMacedonianEx]:
            result['JustificationIL'] = result['Text']
            result['JustificationEN'] = result['Text']
        if version == Version.v2017:
            if self.status is not None:
                result['Status'] = self.status.to_dict()
        elif version in [Version.v2018, Version.v2018_dry, Version.vMacedonianEx]:
            if self.is_issue():
                result['Status'] = self.status.issue_status
                result['Urgent'] = self.status.urgent_status
            elif self.is_need():
                result['Status'] = self.status.need_status
                result['Resolution'] = self.status.relief_status
                result['Urgent'] = self.status.urgent_status
        else:
            raise Exception('Unknown version: {}'.format(version))
        if self.keywords is not None:
            if type(self.keywords) is str:
                result['Keyword'] = self.keywords
            result['Keyword'] = [keyword if type(keyword) is str else keyword.to_dict() for keyword in self.keywords]
        if hasattr(self, 'unknown_attributes'):
            result.update(self.unknown_attributes)
        return result

    def assign_place_mention(self, entities):
        place_id = self.place_id
        place_mention = None
        # Has place_id, and we are given the dict/list of entities, find the correct mention and assign it
        if hasattr(entities, 'keys'): 
            # Assume a dict (by ent_id)
            if place_id in entities:
                self.place_mention = list(sorted(entities[place_id], key=lambda x:x.men_status != 'representative'))[0]
            else:
                print('Place ID "{}" not found in gold entity list'.format(place_id))
        else: # Assume list
            if not hasattr(assign_place_mention, '_warned') or not assign_place_mention._warned:
                print('lor_utils.py:assign_place_mention -> WARNING: using list to find entity, this will be slow.')
                assign_place_mention._warned = True
            for mention in entities:
                if mention.ent_id == place_id:
                    self.place_mention = mention
                    break
        return place_mention
    
    def generate_default_status(self):
        if self.is_need():
            self.status = StatusNeed()
        else:
            self.status = StatusIssue()

    @classmethod
    def from_dict(cls, sf_dict, documents={}, mentions_by_doc_and_seg={}):
        used_keys = set()
        result = SituationFrame(None, None, None, None, None, None)
        if 'DocumentID' in sf_dict:
            result.doc_id = sf_dict['DocumentID']
            used_keys.add('DocumentID')
        if 'SegmentID' in sf_dict:
            # Version v2017
            result.seg_id = sf_dict['SegmentID']
            used_keys.add('SegmentID')
        if 'Justification' in sf_dict:
            # Version v2018_dry
            try:
                result.seg_id = sf_dict['Justification']['SegmentID']
            except:
                result.seg_id = sf_dict['Justification']
            used_keys.add('Justification')
        if 'Justification_ID' in sf_dict:
            # Version v2018
            result.seg_id = sf_dict['Justification_ID']
            used_keys.add('Justification_ID')
        if 'JustificationIL' in sf_dict:
            result.justification_il = sf_dict['JustificationIL']
            used_keys.add('JustificationIL')
        if 'JustificationEN' in sf_dict:
            result.justification_en = sf_dict['JustificationEN']
            used_keys.add('JustificationEN')
        if result.seg_id is not None:
            result.frame_id = '{}:{}'.format(result.doc_id, result.seg_id.replace(' ', '_'))
        if 'Type' in sf_dict:
            result.type = sf_dict['Type']
            used_keys.add('Type')
        if 'Source' in sf_dict:
            result.source = sf_dict['Source']
            used_keys.add('Source')
        if 'TypeConfidence' in sf_dict:
            result.type_confidence = sf_dict['TypeConfidence']
            used_keys.add('TypeConfidence')
        if 'Confidence' in sf_dict:
            result.type_confidence = sf_dict['Confidence']
            used_keys.add('Confidence')
        if 'Text' in sf_dict:
            result.text = sf_dict['Text']
            used_keys.add('Text')
        if result.doc_id in documents and result.seg_id is not None:
            result.text = ' ||| '.join(documents[result.doc_id].get_segment(seg_id).text for seg_id in re.split(r'(\t| \|\|\| )', result.seg_id) 
                                       if documents[result.doc_id].get_segment(seg_id) is not None)
        if 'Keyword' in sf_dict:
            if isinstance(sf_dict['Keyword'], list):
                result.keywords = [Keyword.from_dict(keyword) for keyword in sf_dict['Keyword']]
            else:
                result.keywords = [Keyword(keyword, None, None, None) for keyword in sf_dict['Keyword'].split(';')]
            used_keys.add('Keyword')
        if 'Status' in sf_dict:
            if type(sf_dict['Status']) == str:
                # Version v2018
                if result.is_issue():
                    if 'Urgency' in sf_dict:
                        urgency = sf_dict['Urgency']
                        used_keys.add('Urgency')
                    elif 'Urgent' in sf_dict:
                        urgency = sf_dict['Urgent']
                        used_keys.add('Urgent')
                    else:
                        urgency = True
                    result.status = StatusIssue(sf_dict['Status'], urgent_status=urgency)
                else:
                    if 'Relief' in sf_dict:
                        resolution = sf_dict['Relief']
                        used_keys.add('Relief')
                    elif 'Resolution' in sf_dict:
                        resolution = sf_dict['Resolution']
                        used_keys.add('Resolution')
                    else:
                        resolution = None
                    if 'Urgency' in sf_dict:
                        urgency = sf_dict['Urgency']
                        used_keys.add('Urgency')
                    elif 'Urgent' in sf_dict:
                        urgency = sf_dict['Urgent']
                        used_keys.add('Urgent')
                    else:
                        urgency = True
                    result.status = StatusNeed(sf_dict['Status'], resolution, urgency)
                    result.resolution_status = resolution
                    result.urgency_status = urgency
            else:
                # Version v2017
                result.status = Status.from_dict(sf_dict['Status'])
                if result.is_need():
                    result.resolution_status = result.status.relief_status
                result.urgency_status = result.status.urgent_status
            used_keys.add('Status')
        else:
            result.generate_default_status()
        result.place_mention = None
        if 'Place' in sf_dict:
            # Version v2018
            result.place_mention = Mention.from_text(sf_dict['Place'], documents, mentions_by_doc_and_seg,
                                                     result.doc_id, result.seg_id)
            used_keys.add('Place')
        if 'PlaceMention' in sf_dict:
            # Version v2017 or complete internal version
            result.place_mention = Mention.from_dict(sf_dict['PlaceMention'], documents, mentions_by_doc_and_seg,
                                                     result.doc_id, result.seg_id)
            used_keys.add('PlaceMention')
        if 'Place_KB_ID' in sf_dict:
            if result.place_mention is not None:
                result.place_mention.kb_id = sf_dict['Place_KB_ID']
            result.kb_id = sf_dict['Place_KB_ID']
            used_keys.add('Place_KB_ID')
        unknown_attributes = {}
        for key, value in sf_dict.items():
            if key in used_keys:
                continue
            unknown_attributes[key] = value
        result.unknown_attributes = unknown_attributes
        if len(unknown_attributes) > 0 and 'unknown_attributes' not in SituationFrame.warnings:
            print('WARNING: unknown attributes: "{}"'.format('", "'.join(str(v) for v in unknown_attributes.keys())), file=sys.stderr)
            SituationFrame.warnings['unknown_attributes'] = True
        return result

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result
    
    def __repr__(self):
        return str(self.to_complete_dict())

    __str__ = __repr__


def tprint(message):
    """A quick method to print messages prepended with time information"""
    print('[{}]{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], message))

class Timing(object):
    """A context manager that prints the execution time of the block it manages"""

    def __init__(self, message, logger=None, one_line=True):
        self.message = message
        if logger is not None:
            self.default_logger = False
            self.one_line = False
            self.logger = logger
        else:
            self.default_logger = True
            self.one_line = one_line
            self.logger = None

    def _log(self, message, newline=True):
        if self.default_logger:
            print(message, end='\n' if newline else '')
            sys.stdout.flush()
        else:
            self.logger.info(message)

    def __enter__(self):
        self.start = time.time()
        self._log(self.message, not self.one_line)

    def __exit__(self, exc_type, exc_value, traceback):
        self._log('{}Done in {:.3f}s'.format('' if self.one_line else self.message, time.time()-self.start))

def read_kb_file(in_path, brief=False):
    """Reads a KB entities file

    If brief=True: The returned KBEntry objects have reduced fields only until latitude and longitude
    """
    result = OrderedDict()
    with codecs.open(in_path, 'r', encoding='utf-8') as infile:
        headers = infile.readline()
        for line in infile:
            kb_entry = KBEntry(*line.strip('\n').split('\t'), brief=brief)
            result[kb_entry.entityid] = kb_entry
    return result

def read_ltf(in_path, ignore_int=False):
    """Reads an ltf file and returns a Document object containing list of Segment objects
    """
    if ignore_int:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    with codecs.open(in_path, 'r', encoding='utf-8') as infile:
        soup = BS(infile.read(), 'lxml')
    segments = []
    doc = soup.find('doc')
    doc_id = doc['id']
    try:
        lang = doc['lang']
    except:
        lang = ''
    tokenization = doc.get('tokenization', 'none')
    grammar = doc.get('grammar', 'none')
    raw_text_len = int(doc.get('raw_text_char_length', '0'))
    raw_text_md5 = doc.get('raw_text_md5', 'none')
    for segment in soup.find_all('seg'):
        seg_id = segment['id']
        start_char = int(segment['start_char'])
        end_char = int(segment['end_char'])
        seg_text = segment.find('original_text').get_text()
        tokens = []
        tok_spans = []
        for token in segment.find_all('token'):
            tok_text = token.get_text()
            tok_id = token['id']
            tok_pos = token.get('pos', 'none')
            tok_morph = token.get('morph', 'none')
            tok_start = int(token['start_char'])
            tok_end = int(token['end_char'])
            token_obj = Token(tok_id, tok_pos, tok_morph, Span(tok_start, tok_end), tok_text)
            tokens.append(token_obj)
            tok_spans.append(token_obj.span)
        segments.append(Segment(seg_id, seg_text, Span(start_char, end_char), tokens, tok_spans, in_path))
    return Document(doc_id, lang, tokenization, grammar, raw_text_len, raw_text_md5, segments)

def read_ltf_files(in_dir_or_list, ext_filter='.ltf.xml', progress_bar=True, outtype='list', n_jobs=8, limit=-1):
    """Read all LTF documents in the given directory (or a file list), returns a list of documents, sorted by doc_id

    By default will use all files in the given directory ending with .ltf.xml.
    Specify extension using ext_filter, or put None to use all files.

    By default will show a progress bar, disable by passing progress_bar=False

    If outtype='list', return a list containing Document objects
    If outtype='generator', yield a Document one at a time, so as not to load everything at once
    If outtype='dict', return an OrderedDict() object containing mapping from document IDs to Document objects
    """
    if outtype not in ['list', 'dict', 'generator']:
        raise ValueError('outtype for reading LTF documents not recognized: {}'.format(outtype))
    if outtype == 'list':
        result = []
    elif outtype == 'dict':
        result = OrderedDict()
    if isinstance(in_dir_or_list, string_types): # A directory name
        filename_iter = sorted(os.listdir(in_dir_or_list))
        if ext_filter is not None:
            filename_iter = ['{}/{}'.format(in_dir_or_list, filename) for filename in filename_iter if filename.endswith(ext_filter)]
    else: # A list
        filename_iter = in_dir_or_list
    if limit >= 0:
        filename_iter = filename_iter[:limit]
    if progress_bar:
        filename_iter = tqdm(filename_iter, smoothing=0.1)
    if outtype == 'generator':
        n_jobs = 1
    if n_jobs > 1:
        pool = Pool(processes=n_jobs)
        try:
            for document in pool.map(partial(read_ltf, ignore_int=True), filename_iter, 2):
                if outtype == 'list':
                    result.append(document)
                elif outtype == 'dict':
                    result[document.doc_id] = document
            pool.terminate()
        except KeyboardInterrupt:
            pool.terminate()
            raise
    else:
        if outtype == 'generator':
            def _retval():
                for filename in filename_iter:
                    yield read_ltf(filename)
            return _retval()
        for filename in filename_iter:
            document = read_ltf(filename)
            if outtype == 'list':
                result.append(document)
            elif outtype == 'dict':
                result[document.doc_id] = document
    return result

def read_alignment(in_path):
    with open(in_path, 'r') as infile:
        soup = BS(infile.read(), 'lxml')
    alignments = soup.find('alignments')
    source_id = alignments['source_id']
    translation_id = alignments['translation_id']
    alignments_list = []
    for alignment in alignments.find_all('alignment'):
        alignments_list.append((alignment.source['segments'].split(' '), alignment.translation['segments'].split(' ')))
    return Alignment(source_id, translation_id, alignments_list)

def read_alignments(in_dir, source_doc_ids=None, translation_doc_ids=None):
    source_mapping, translation_mapping = {}, {}
    for filename in tqdm(os.listdir(in_dir), smoothing=0.1):
        doc_id = filename[:filename.find('.aln.xml')]
        if source_doc_ids is not None and doc_id not in source_doc_ids:
            continue
        alignment = read_alignment('{}/{}'.format(in_dir, filename))
        source_id = alignment.source_id
        translation_id = alignment.translation_id
        source_mapping[source_id] = alignment
        translation_mapping[translation_id] = alignment
    return source_mapping, translation_mapping

def read_ner_file(in_path, format='tsv', outtype='list'):
    """Reads EDL file in tab-separated format (e.g., il5_edl.tab)

    If outtype='list', return a list containing the mentions
    If outtype='dict', return an OrderedDict() object containing mapping from mention IDs to Mention objects
    """
    if outtype not in ['list', 'dict']:
        raise ValueError('outtype for reading NER file not recognized: {}'.format(outtype))
    if outtype == 'list':
        result = []
    elif outtype == 'dict':
        result = OrderedDict()
    with codecs.open(in_path, 'r', encoding='utf-8') as infile:
        first = True
        while True:
            line = infile.readline()
            if line == '':
                break
            if first and line.startswith('system_run_id'):
                first = False
                continue
            first = False
            line = line.strip()
            sys_id, men_id, men_text, extent, kb_id, ent_type, men_type, conf = line.split('\t')[:8]
            doc_id, extent = extent.split(':')
            start, end = map(int, extent.split('-'))
            conf = float(conf)
            mention = Mention(sys_id, doc_id, men_id, men_text, Span(start, end), kb_id, ent_type, men_type, conf)
            if outtype == 'list':
                result.append(mention)
            elif outtype == 'dict':
                result[men_id] = mention
    return result

def read_sf_mentions(in_path, outtype='list'):
    """Reads a single file in "mentions" folder in sf_anno directory (the file containing list of mentions)

    The file is assumed to be in TSV format (with .tab extension)

    Returns a list of Entity objects or a dict of Entity objects grouped by entity_id
    outtype: ['list', 'dict']
    """
    if outtype not in ['list', 'dict']:
        raise ValueError('outtype for reading NER file not recognized: {}'.format(outtype))
    if outtype == 'list':
        result = []
    elif outtype == 'dict':
        result = OrderedDict()
    with codecs.open(in_path, 'r', encoding='utf-8') as infile:
        headers = infile.readline()
        while True:
            line = infile.readline()
            if line == '':
                break
            line = line.strip()
            doc_id, ent_id, men_id, ent_type, men_status, start, end, men_text = line.split('\t')[:8]
            entity = Entity(doc_id, ent_id, men_id, ent_type, men_status, Span(int(start), int(end)), men_text)
            if outtype == 'list':
                result.append(entity)
            elif outtype == 'dict':
                if ent_id not in result:
                    result[ent_id] = []
                result[ent_id].append(entity)

    return result

def read_sf_mentions_dir(in_dir, outtype='list'):
    """Reads "mentions" folder in a situation frame annotation directory (the one containing "issues", "needs", and "mentions")

    Returns a list of Entity object (list) or a dict of Entity objects grouped by entity_id (dict)
    outtype: ['list', 'dict']
    """
    if outtype not in ['list', 'dict']:
        raise ValueError('outtype for reading NER file not recognized: {}'.format(outtype))
    if outtype == 'list':
        result = []
    elif outtype == 'dict':
        result = OrderedDict()
    for filename in os.listdir(in_dir):
        entities = read_sf_mentions('{}/{}'.format(in_dir, filename), outtype=outtype)
        if outtype == 'list':
            result.extend(entities)
        else:
            for entity_id, mentions in entities.items():
                if entity_id in result:
                    result[entity_id].extend(mentions)
                else:
                    result[entity_id] = mentions
    return result

def read_sf_anno(in_path, outtype='list', documents={}):
    """Reads SF gold annotation file (in sf_anno folder) and returns them as list or dict

    The SF gold annotation file can either be "issues" or "needs", this handles both.
    The first line in the document would be a header line (tab-separated)
    The subsequent lines will contain the value according to the headers.
    For issues:
        (2016) doc_id, frame_id, frame_type, issue_type, place_id, proxy_status, issue_status, description
        (2017) user_id, doc_id, frame_id, frame_type, issue_type, place_id, proxy_status, issue_status, description
        (2018) user_id, doc_id, frame_id, frame_type, issue_type, place_id, proxy_status, issue_status, scope, severity, description, kb_id
    For needs:
        (2016) doc_id, frame_id, frame_type, need_type, place_id, proxy_status, need_status, urgency_status, resolution_status, reported_by, resolved_by, description
        (2017) user_id, doc_id, frame_id, frame_type, need_type, place_id, proxy_status, need_status, urgency_status, resolution_status, reported_by, resolved_by, description
        (2018) user_id, doc_id, frame_id, frame_type, need_type, place_id, proxy_status, need_status, scope, severity, resolution_status, reported_by, resolved_by, description, kb_id

    If outtype='list': output a list of SFs
    If outtype='dict': output a nested dict of SFs grouped by doc ID and then type
    """
    if outtype not in ['list', 'dict']:
        raise ValueError('outtype for reading NER file not recognized: {}'.format(outtype))
    if outtype == 'list':
        result = []
    elif outtype == 'dict':
        result = OrderedDict()
    with codecs.open(in_path, 'r', encoding='utf-8') as infile:
        headers = infile.readline().split('\t')
        is_issue = False  # Needs type
        if len(headers) in [8, 9, 12] and 'issue_type' in headers:
            is_issue = True # Issues type
        elif len(headers) in [12, 13, 15] and 'need_type' in headers:
            is_issue = False
        else:
            raise ValueError(('The file {} is not in the correct format for SF gold annotation'
                              ' of either issue or need type').format(in_path))
        if 'scope' in headers:
            use_scope_severity = True
        else:
            use_scope_severity = False

        while True:
            line = infile.readline()
            if line == '':
                break
            line = line.strip()
            if is_issue:
                if use_scope_severity:
                    (user_id, doc_id, frame_id, frame_type, issue_type, place_id, proxy_status,
                            issue_status, scope, severity, description, kb_id) = line.split('\t')[:12]
                else:
                    try:
                        (user_id, doc_id, frame_id, frame_type, issue_type, place_id, proxy_status, 
                                issue_status, description) = line.split('\t')[:9]
                    except:
                        (doc_id, frame_id, frame_type, issue_type, place_id, proxy_status, 
                                issue_status, description) = line.split('\t')[:8]
                        user_id = None
                    scope = None
                    severity = None
                    kb_id = None
                sf = SituationFrame(user_id, doc_id, frame_id, frame_type, place_id, proxy_status,
                                    issue_type=issue_type, issue_status=issue_status,
                                    description=description, scope=scope, severity=severity, kb_id=kb_id,
                                    documents=documents)
            else:
                if use_scope_severity:
                    (user_id, doc_id, frame_id, frame_type, need_type, place_id, proxy_status,
                            need_status, scope, severity, resolution_status, reported_by, resolved_by,
                            description, kb_id) = line.split('\t')[:15]
                    urgency_status = SituationFrame.get_urgency(scope, severity)
                else:
                    try:
                        (user_id, doc_id, frame_id, frame_type, need_type, place_id, proxy_status,
                                need_status, urgency_status, resolution_status, reported_by, resolved_by,
                                description) = line.split('\t')[:13]
                    except:
                        (doc_id, frame_id, frame_type, need_type, place_id, proxy_status,
                                need_status, urgency_status, resolution_status, reported_by, resolved_by,
                                description) = line.split('\t')[:12]
                        user_id = None
                    scope = None
                    severity = None
                    kb_id = None
                sf = SituationFrame(user_id, doc_id, frame_id, frame_type, place_id, proxy_status,
                                    need_type=need_type, need_status=need_status,
                                    urgency_status=urgency_status not in ['false', 'False', False],
                                    resolution_status=resolution_status, reported_by=reported_by,
                                    resolved_by=resolved_by, description=description, scope=scope,
                                    severity=severity, kb_id=kb_id, documents=documents)
            if outtype == 'list':
                result.append(sf)
            elif outtype == 'dict':
                if sf.doc_id not in result:
                    result[sf.doc_id] = {}
                if sf.type not in result[doc_id]:
                    result[sf.doc_id][sf.type] = []
                result[sf.doc_id][sf.type].append(sf)
    return result

def read_sf_annos(sf_anno_dir, subdirs=['issues', 'needs'], outtype='list', documents={}):
    """Reads the SF annotations in the sf_anno/ directory, containing issues/ and needs/ directories

    subdirs can be specified to consider only specific subdirectory. Otherwise issues/ and needs/ are used.
    """
    if outtype not in ['list', 'dict']:
        raise ValueError('outtype for reading NER file not recognized: {}'.format(outtype))
    if outtype == 'list':
        result = []
    elif outtype == 'dict':
        result = OrderedDict()
    filenames = []
    for subdir in subdirs:
        filenames.extend(['{}/{}/{}'.format(sf_anno_dir, subdir, filename) for filename in os.listdir('{}/{}'.format(sf_anno_dir, subdir))])
    for filename in filenames:
        if outtype == 'list':
            result.extend(read_sf_anno(filename, outtype=outtype, documents=documents))
        elif outtype == 'dict':
            for doc_id, sf_type_to_sfs in read_sf_anno(filename, outtype=outtype, documents=documents).items():
                result[doc_id] = sf_type_to_sfs
    try:
        entities = read_sf_mentions_dir('{}/mentions'.format(sf_anno_dir), outtype='dict')
        if outtype == 'list':
            sf_iter = iter(result)
        elif outtype =='dict':
            def _iter_dict():
                for doc_id, sf_type_to_sfs in result.items():
                    for sf_type, sfs in sf_type_to_sfs.items():
                        for sf in sfs:
                            yield sf
            sf_iter = _iter_dict()
        for sf in sf_iter:
            if sf.place_id is not None and sf.place_id != 'none':
                sf.assign_place_mention(entities)
    except:
        pass
    return result

SF_TYPES = ['terrorism', 'crimeviolence', 'regimechange', 'food', 'water', 'med', 'infra', 'shelter', 'evac', 'utils', 'search']
SF_TYPES_VOCAB = dict([(sf_type, idx) for (idx, sf_type) in enumerate(SF_TYPES)])

def vectorize(sfs, dids, include_place=False, binary=False):
    """Convert a list of SFs and a list of document IDs into DocID-SFType matrix

    Args:
        binary (bool): Whether to have binary matrix or actual count
    """
    did_indexer = {did: i for i, did in enumerate(dids)}
    did_source_pair = set()
    if include_place:
        mat = np.zeros((len(dids), len(SF_TYPES)))
    else:
        mat = np.zeros((len(dids), len(SF_TYPES)))
    for sf in sfs:
        did = sf['DocumentID']
        if did not in did_indexer:
            continue
        did_idx = did_indexer[did]
        source = sf.get('Source', '')
        sf_type = sf['Type']
        if sf_type not in SF_TYPES_VOCAB:
            continue
        key = (did, source, sf_type)
        if key in did_source_pair:
            continue
        did_source_pair.add(key)
        type_idx = SF_TYPES_VOCAB[sf_type]
        if binary:
            mat[did_idx, type_idx] = 1
        else:
            mat[did_idx, type_idx] += 1
    return mat

def score_sf(preds, gold, include_place=False, metric='occwf1', doc_prefix='', verbose=False):
    dids = set([sf['DocumentID'] for sf in preds if sf['DocumentID'].startswith(doc_prefix)] \
               + [sf['DocumentID'] for sf in gold if sf['DocumentID'].startswith(doc_prefix)])
    dids = sorted(list(dids))
    if metric == 'occwf1':
        binary = False
    else:
        binary = True

    preds_mat = vectorize(preds, dids, binary=True)
    gold_mat = vectorize(gold, dids, binary=binary)

    preds_mat = preds_mat.flatten()
    gold_mat = gold_mat.flatten()

    gold_mask = np.where(gold_mat != 0, np.ones_like(gold_mat), np.zeros_like(gold_mat))
    pred_mask = np.where(preds_mat != 0, np.ones_like(preds_mat), np.zeros_like(preds_mat))

    tp_mask = np.multiply(pred_mask, gold_mask)
    fp_mask = pred_mask - tp_mask
    fn_mask = gold_mask - tp_mask

    if verbose:
        from pprint import pprint
        try:
            idx = dids.index('IL9_WL_020642_20161112_I0040RL62')
        except:
            idx = -1
        print(dids[idx])
        print('Gold anno:', end=' ')
        pprint(gold_mat.reshape((len(fp_mask)//11, 11)).tolist()[idx])
        print('Pred anno:', end=' ')
        pprint(preds_mat.reshape((len(fp_mask)//11, 11)).tolist()[idx])
        print('TP mask:  ', end=' ')
        pprint(tp_mask.reshape((len(fp_mask)//11, 11)).tolist()[idx])
        print('FP mask:  ', end=' ')
        pprint(fp_mask.reshape((len(fp_mask)//11, 11)).tolist()[idx])
        print('FN mask:  ', end=' ')
        pprint(fn_mask.reshape((len(fp_mask)//11, 11)).tolist()[idx])

    tp = np.multiply(tp_mask, gold_mat).sum()
    fp = fp_mask.sum()
    fn = np.multiply(fn_mask, gold_mat).sum()
    tot_pred = tp+fp
    tot_gold = tp+fn

    if tot_pred == 0:
        prec = 0
    else:
        prec = tp/tot_pred
    if tot_gold == 0:
        rec = 0
    else:
        rec = tp/tot_gold

    if prec*rec == 0:
        f1 = 0
    else:
        f1 = 2 * (prec * rec) / (prec + rec)
    return prec, rec, f1, tp, fp, fn

def main():
    pass

if __name__ == '__main__':
    main()

