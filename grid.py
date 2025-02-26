import pygame
from pytmx.util_pygame import load_pygame
from enum import Enum
from sprites import Generic
from event_sprites import FireSprite, CoinSprite, SnowPuddleSprite
from quest import InteractQuest
from settings import *
from timer import Timer
import threading

from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display

from langgraph.checkpoint.memory import MemorySaver

class GridItem(Enum):
    COLLISION = 0
    FIRE_SPRITE = 1    
    COIN_SPRITE = 2
    SNOW_PUDDLE_SPRITE = 3

EVENT = {
    GridItem.FIRE_SPRITE: "Put out the fire"
}

class Grid:
    def __init__(self, player, all_sprites, interaction_sprites, get_npc_by_name, start_event, get_locations):
        self.display_surface = pygame.display.get_surface()
        self.player = player
        self.all_sprites = all_sprites
        self.interaction_sprites = interaction_sprites
        self.get_npc_by_name = get_npc_by_name
        self.start_event = start_event
        self.get_locations = get_locations
        self.create_collision_grid()
        self.build_graph()
        
        self.event_timer = Timer(15000, self.trigger_event) # Timer need to be at least 15s, for llm to generate event and quest
        self.event_timer.activate()
        self.target_npc = self.get_npc_by_name("Alice")
    
    def create_collision_grid(self):
        # Use for calculating path for movement
        ground = pygame.image.load('./graphics/world/ground.png')
        self.h_tiles, self.v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        self.grid = [[[] for _ in range(self.h_tiles)] for _ in range(self.v_tiles)]
        for x, y, _ in load_pygame('./data/map.tmx').get_layer_by_name('Collision').tiles():
            self.grid[y][x].append(GridItem.COLLISION)
            # black_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            # black_surface.fill((0, 0, 0))
            # Generic((x * TILE_SIZE, y * TILE_SIZE), black_surface, self.all_sprites)
    
    def get_current_grid(self) -> list:
        """
        Get the 2D grid of the current game world
        """
        return self.grid
    
    def add_to_grid(self, sprite: int, positions: list) -> str:
        """
        Add a sprite to a 2D grid of the game world
        
        Args:
            sprite: integer in a list of Grid Items (e.g. 1 for GridItem.FIRE_SPRITE)
            positions: a list of positions with (x-coordinate, y-coordinate) tuple. An example is [(2,3), (6,7)]
        """
        for pos in positions:
            x, y = pos
            
            if sprite == GridItem.FIRE_SPRITE.value:
                FireSprite((x, y), [self.all_sprites, self.interaction_sprites], self.player)
            elif sprite == GridItem.COIN_SPRITE.value:
                CoinSprite((x, y), [self.all_sprites, self.interaction_sprites], self.player)
            elif sprite == GridItem.SNOW_PUDDLE_SPRITE.value:
                SnowPuddleSprite((x, y), [self.all_sprites, self.interaction_sprites], self.player)
        
        return {GridItem(sprite).name}
    
    def generate_event(self, event_name: str, event_description: str, event_outcome: str) -> dict:
        """
        Generate an event inside the game world
        
        Args:
            event_name: event name with max 4 words
            event_description: brief description of story behind the event
            event_outcome: outcome of event (e.g. can be "positive", "negative" or "netural)
        """
        event = {
            "event_name": event_name,
            "event_description": event_description,
            "event_outcome": event_outcome
        }
        self.start_event(event_name, event_description, "Alice")
        return event
    
    def generate_quest_for_npc(self, quest_name: str, quest_description: str, interaction_object: str, target_quantity: int):
        """
        Assign a quest to npc inside the game world, so player can handle the event and earn reward
        
        Args:
            quest_name: Clear short name for quest
            quest_description: Describe the event briefly and state how player can help to handle the event
            interaction_object: name of the interaction object in the event (use output from "add_to_grid" tool)
            target_quantity: number of interaction object in the event
        """
        print(f"quest name: {quest_name}, quest description: {quest_description}, interaction_object: {interaction_object}, qty: {target_quantity}")
        rewards = [{"money": 100}, {"experience": 5}, {"name": "corn", "type": "resource", "quantity": 5}] # Hard-coded
        quest = InteractQuest(self.target_npc.npc_personality['name'], quest_name, quest_description, interaction_object.lower(), rewards, target_quantity)
        self.target_npc.assign_quest(quest)
    
    def build_graph(self):
        tools = [self.add_to_grid, self.generate_event, self.generate_quest_for_npc]
        llm = ChatOpenAI(model="gpt-4o")
        llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
        
        # System message
        sys_msg = SystemMessage(content=f"""
        You are a game master in the 2D world of Pydew.
        Your role is to create random events for the game.
        When creating a random events. Use tools calling to modify the game environment.
        
        The size of grid is restricted to {self.h_tiles * TILE_SIZE} for x-coordinates and {self.v_tiles * TILE_SIZE} for y-coordinates.
        The sprite element you can add is limited to a list here: {list(GridItem)}
        Feel free to call the tools more than once.
        
        Here is the list of polygons for different locations. Use it when creating event:
        {self.get_locations()}
        
        For quest generation, here is how player can interact with the event. For large locations, can specify the directions (e.g. northeast, south)
        {EVENT}
        """)

        # Node
        def assistant(state: MessagesState):
           return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}
    
        # Graph
        builder = StateGraph(MessagesState)

        # Define nodes: these do the work
        builder.add_node("assistant", assistant)
        builder.add_node("tools", ToolNode(tools))
        
        # Define edges: these determine how the control flow moves
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges(
            "assistant",
            # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
            # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
            tools_condition,
        )
        builder.add_edge("tools", "assistant")
        
        # Build persistence
        memory = MemorySaver()
        self.config = {"configurable": {"thread_id": "1"}} # Specify a thread
        
        self.react_graph = builder.compile(checkpointer=memory)

    def process_input(self, query):
        messages = [HumanMessage(content=query)]
        messages = self.react_graph.invoke({"messages": messages}, self.config)
        # for m in messages['messages']:
        #     m.pretty_print()
    
    def get_human_input(self, query, delay=1.0):
        timer = threading.Timer(delay, self.process_input, args=[query])
        timer.start()
        
    def trigger_event(self, delay=1.0):
        if self.target_npc.quest != None:
            return
        print('trigger event')
        query = "Generate a event and a quest"
        timer = threading.Timer(delay, self.process_input, args=[query])
        timer.start()

    def update(self):
        self.event_timer.update()
        
        if not self.event_timer.active:
            self.event_timer.activate()
