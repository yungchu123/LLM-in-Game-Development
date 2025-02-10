from enum import Enum
from abc import ABC, abstractmethod

class QuestStatus(Enum):
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    REWARD_ACCEPTED = 3

class Quest:
    def __init__(self, npc_name, rewards):
        self.rewards = rewards
        self.npc_name = npc_name
        
        self.name = None
        self.objective = None  # e.g., "collect", "defeat", "talk"
        self.target_quantity = 1
        
        # Check progress
        self.current_state = None
        self.progress = 0
        
        self.reward = None  # e.g., {"money": 50, "item": "sword"}
        self.status = QuestStatus.NOT_STARTED

    @abstractmethod
    def start_quest(self, player):
        """Must be overridden by subclasses"""
        pass
    
    @abstractmethod
    def update_progress(self, player):
        """Must be overridden by subclasses"""
        pass

    def grant_reward(self, player):
        """Grant reward to the player if the quest is completed."""
        if self.status == QuestStatus.COMPLETED:
            for reward in self.rewards:
                if "money" in reward:
                    player.money += reward["money"]
                else:
                    player.add_to_inventory(reward["name"], reward["type"], reward["quantity"])
            player.completed_quests.append(self)
            print(f"Quest for {self.npc_name} '{self.name}' completed! Rewards granted.")
            self.status = QuestStatus.REWARD_ACCEPTED
        else:
            print(f"Quest for {self.npc_name} '{self.name}' is not yet completed.")
            
class TalkQuest(Quest):
    def __init__(self, npc_name, target_npc, rewards):
        super().__init__(npc_name, rewards)
        self.name = f"Talk to {target_npc}"
        self.objective = 'talk'
        self.target_npc = target_npc

    def start_quest(self, player):
        # When accepted by player
        if self.target_npc not in player.talked_to_npcs:
            player.talked_to_npcs[self.target_npc] = 0    
        self.current_state = player.talked_to_npcs[self.target_npc]
        self.status = QuestStatus.IN_PROGRESS

    def update_progress(self, player):
        if self.status != QuestStatus.IN_PROGRESS:
            return
        # Check for completion
        if player.talked_to_npcs[self.target_npc] > self.current_state:
            self.status = QuestStatus.COMPLETED
            print(self.status)

class CollectQuest(Quest):
    def __init__(self, npc_name, item_name, item_type, rewards, target_quantity=1):
        super().__init__(npc_name, rewards)
        self.name = f"Collect {target_quantity} {item_name} for me"
        self.objective = 'collect'
        self.target_quantity = target_quantity
        self.item_name = item_name
        self.item_type = item_type
    
    def start_quest(self, player):
        # When accepted by player
        item = player.get_item(self.item_name, self.item_type)
        
        if item:
            self.current_state = item["quantity"]
        else:
            player.add_to_inventory(self.item_name, self.item_type, 0)
            self.current_state = 0 
        print(f"Quest for {self.npc_name} '{self.name}' accepted")
        self.status = QuestStatus.IN_PROGRESS

    def update_progress(self, player):
        if self.status != QuestStatus.IN_PROGRESS:
            return
        
        # Update progress
        item_quantity = player.get_item(self.item_name, self.item_type)["quantity"]
        if item_quantity > self.current_state:
            self.progress += (item_quantity - self.current_state)
            print(f'{self.progress}/{self.target_quantity}')
        self.current_state = item_quantity
        
        # Check for completion
        if self.progress >= self.target_quantity:
            self.status = QuestStatus.COMPLETED
            print(self.status)
