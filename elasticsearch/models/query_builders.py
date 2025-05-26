"""Query builder classes for ElasticSearch queries."""

class MatchQuery:
    """Builds a match query for text fields."""
    def __init__(self, field, query, fuzziness=None):
        self.field = field
        self.query = query
        self.fuzziness = fuzziness
    
    def to_dict(self):
        query_dict = {"query": self.query}
        if self.fuzziness:
            query_dict["fuzziness"] = self.fuzziness
        return {"match": {self.field: query_dict}}

class MatchPhraseQuery:
    """Builds a match phrase query for exact text matching."""
    def __init__(self, field, query):
        self.field = field
        self.query = query
    
    def to_dict(self):
        return {"match_phrase": {self.field: {"query": self.query}}}

class RangeQuery:
    """Builds a range query for numeric and date fields."""
    def __init__(self, field, gte=None, lte=None):
        self.field = field
        self.gte = gte
        self.lte = lte
    
    def to_dict(self):
        range_dict = {}
        if self.gte is not None:
            range_dict["gte"] = self.gte
        if self.lte is not None:
            range_dict["lte"] = self.lte
        return {"range": {self.field: range_dict}}

class TermQuery:
    """Builds a term query for exact value matching."""
    def __init__(self, field, value):
        self.field = field
        self.value = value
    
    def to_dict(self):
        return {"term": {self.field: self.value}} 