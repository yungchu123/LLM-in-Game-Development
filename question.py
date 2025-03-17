import random

class Question:
    question_counter = 0
    
    def __init__(self, question_text, topic, hint, explanation, options=None, correct_answer=None):
        """
        Initializes a question object.
        
        :param question_text: The question to be asked.
        :param topic: The topic of the question (e.g., Algebra, Geometry).
        :param hint: A hint to help the player.
        :param explanation: Step-by-step explanation of the answer.
        :param q_type: Type of the question ("open-ended" or "multiple-choice").
        :param options: A list of choices for multiple-choice questions.
        :param correct_answer: The correct answer 
        """
        self.id = Question.question_counter  # Assign unique quest ID
        Question.question_counter += 1
        
        self.question_text = question_text
        self.topic = topic
        self.hint = hint
        self.hint_unlocked = False
        self.fifty_fifty_unlocked = False
        self.removed_options = []        # index of removed options from fifty fifty
        self.explanation = explanation
        self.options = options
        self.correct_answer = correct_answer
        self.status = "not attempted"
        self.selected = -1                # Index of option picked

    def __str__(self):
        return f"Qn id: {self.id} | Topic: {self.topic} | Attempted: {self.status} "

    def check_answer(self, user_answer, player):
        """Checks if the answer is correct and provides explanation."""
        self.selected = user_answer
        if str(self.options[user_answer]).strip().lower() == str(self.correct_answer).strip().lower():
            print("✅ Correct!")
            self.handle_correct(player)
            return True
        else:
            print("❌ Incorrect.")
            self.handle_incorrect(player)
            return False
    
    def handle_correct(self, player):
        if self.status != "not attempted": 
            return
        player.add_money(20)
        player.gain_experience(2)
        self.status = "correct"
        player.completed_questions.append(self)
        print([str(q) for q in player.completed_questions])
    
    def handle_incorrect(self, player):
        if self.status != "not attempted": 
            return
        self.status = "incorrect"
        player.completed_questions.append(self)
        print([str(q) for q in player.completed_questions])
        
    def get_hint(self, player):
        if player.money < 50 or self.hint_unlocked:
            return
        
        player.money -= 50
        self.hint_unlocked = True
    
    def get_fifty_fifty(self, player):
        if player.money < 100 or self.fifty_fifty_unlocked:
            return
        
        player.money -= 100
        self.fifty_fifty_unlocked = True
        
        wrong_answer_indexes = [i for i, x in enumerate(self.options) if x != self.correct_answer]
        self.removed_options = random.sample(wrong_answer_indexes, 2)        