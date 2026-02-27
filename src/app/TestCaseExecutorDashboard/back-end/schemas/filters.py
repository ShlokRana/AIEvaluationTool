from pydantic import BaseModel
from typing import Optional, List


class FilterResponse(BaseModel):
    filter_name: str


class AllFiltersResponse(BaseModel):
    domains: List[FilterResponse]
    languages: List[FilterResponse]
    targets: List[FilterResponse]
    plans: Optional[List[FilterResponse]]=[]
    statuses: List[FilterResponse] 
    metrics: Optional[List[FilterResponse]]=[]
      
    
