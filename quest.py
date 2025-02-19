from enum import Enum
from abc import abstractmethod

class QuestStatus(Enum):
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    REWARD_ACCEPTED = 3

class Quest:
    quest_counter = 0 # shared class-level counter
    
    def __init__(self, npc_name, name, description, objective, rewards):
        self.id = Quest.quest_counter  # Assign unique quest ID
        Quest.quest_counter += 1
        
        self.npc_name = npc_name
        self.name = name
        self.description = description
        self.objective = objective  # e.g., "collect", "defeat", "talk"
        self.rewards = rewards
        
        # Check progress
        self.target_item = None
        self.target_quantity = 1
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
            # Grant reward to player
            for reward in self.rewards:
                if "money" in reward:
                    player.add_money(reward["money"])
                else:
                    player.add_to_inventory(reward["name"], reward["type"], reward["quantity"])
           
            # Move quest from active to completed
            player.quests = list(filter(lambda quest: quest.id != self.id, player.quests)) # Remove from active quests
            player.completed_quests.append(self) # Add to completed list
            
            print(f"Quest for {self.npc_name} '{self.name}' completed! Rewards granted.")
            self.status = QuestStatus.REWARD_ACCEPTED
        else:
            print(f"Quest for {self.npc_name} '{self.name}' is not yet completed.")
            
class TalkQuest(Quest):
    def __init__(self, npc_name, target_npc, rewards):
        super().__init__(npc_name, f"Talk to {target_npc}", f"Talk to {target_npc}", 'talk', rewards)
        self.target_npc = target_npc
        self.target_item = target_npc

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
        super().__init__(npc_name, f"Collect {target_quantity} {item_name} for {npc_name}", f"Collect {target_quantity} {item_name}", 'collect', rewards)
        self.target_quantity = target_quantity
        self.target_item = f'{item_name} [{item_type}]'
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

class InteractQuest(Quest):
    def __init__(self, npc_name, quest_name, quest_description, interaction_object, rewards, target_quantity=1):
        super().__init__(npc_name, quest_name, quest_description, 'interact', rewards)
        self.interaction_object = interaction_object
        self.target_quantity = target_quantity
        self.target_item = interaction_object
    
    def start_quest(self, player):
        if self.interaction_object not in player.interacted_obj:
            player.interacted_obj[self.interaction_object] = 0    
        self.current_state = player.interacted_obj[self.interaction_object]
        self.status = QuestStatus.IN_PROGRESS
        
    def update_progress(self, player):
        if self.status != QuestStatus.IN_PROGRESS:
            return
        
        # Update progress
        quantity = player.interacted_obj[self.interaction_object]
        if quantity > self.current_state:
            self.progress += (quantity - self.current_state)
            print(f'{self.progress}/{self.target_quantity}')
        self.current_state = quantity
        
        # Check for completion
        if self.progress >= self.target_quantity:
            self.status = QuestStatus.COMPLETED
            print(self.status)