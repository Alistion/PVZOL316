# services/__init__.py
# 魔法入口：将分散在各个文件中的服务类统一暴露出去

from .Active import ActiveService
from .Arena import ArenaService
from .Auth import AuthService
from .Duty import DutyService
from .Friends import FriendService
from .GM import GMService
from .Instance import InstanceService
from .OpenBox import OpenBoxService
from .Organism import OrganismService
from .Reward import RewardService
from .ServerBattle import ServerBattleService
from .Shop import ShopService
from .Stone import StoneInstance
from .VipService import VipService
from .WorldTree import TreeService
