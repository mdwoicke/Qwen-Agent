import json
from typing import Dict, Iterator, List, Optional, Union

from qwen_agent import Agent
from qwen_agent.llm.base import BaseChatModel
from qwen_agent.llm.schema import (ASSISTANT, CONTENT, DEFAULT_SYSTEM_MESSAGE,
                                   ROLE)
from qwen_agent.memory import Memory
from qwen_agent.prompts import ContinueWriting, WriteFromScratch


class ArticleAgent(Agent):

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE):
        super().__init__(function_list=function_list,
                         llm=llm,
                         system_message=system_message)

        self.mem = Memory(llm=self.llm)

    def _run(self,
             messages: List[Dict],
             lang: str = 'en',
             max_ref_token: int = 4000,
             full_article: bool = False,
             **kwargs) -> Union[str, Iterator[str]]:

        # need to use Memory agent for data management
        *_, last = self.mem.run(messages=messages,
                                max_ref_token=max_ref_token,
                                **kwargs)
        _ref = '\n\n'.join(
            json.dumps(x, ensure_ascii=False) for x in last[-1][CONTENT])

        response = []
        if _ref:
            response.append({
                ROLE:
                ASSISTANT,
                CONTENT:
                f'\n========================= \n> Search for relevant information: \n{_ref}\n'
            })
            yield response

        if full_article:
            writing_agent = WriteFromScratch(llm=self.llm)
        else:
            writing_agent = ContinueWriting(llm=self.llm)
            response.append({
                ROLE:
                ASSISTANT,
                CONTENT:
                '\n========================= \n> Writing Text: \n'
            })
            yield response
        res = writing_agent.run(messages=messages, lang=lang, knowledge=_ref)
        for trunk in res:
            yield response + trunk