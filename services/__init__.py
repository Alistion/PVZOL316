# services/__init__.py
# 魔法入口：将分散在各个文件中的服务类统一暴露出去
from .Shop import ShopService
from .Active import ActiveService
from .WorldTree import TreeService
from .OpenBox import OpenBoxService
from .GM import GMService
from .ServerBattle import ServerBattleService
from .Duty import DutyService
from .VipService import VipService
from .Stone import StoneInstance
from .Instance import InstanceService
from .Arena import ArenaService  