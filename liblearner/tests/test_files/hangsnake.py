class Hangman:
    """A basic Hangman game class."""
    
    def __init__(self, word: str):
        self.word = word
        self.guessed_letters = set()
        self.remaining_attempts = 6

    def guess(self, letter: str) -> bool:
        """Make a guess in the Hangman game.
        
        Args:
            letter: The letter being guessed.
            
        Returns:
            True if the letter is in the word, False otherwise.
        """
        if letter in self.word and letter not in self.guessed_letters:
            self.guessed_letters.add(letter)
            return True
        else:
            self.remaining_attempts -= 1
            return False

    def is_won(self) -> bool:
        """Check if the game is won.
        
        Returns:
            True if all letters are guessed, False otherwise.
        """
        return all(letter in self.guessed_letters for letter in self.word)

    def is_lost(self) -> bool:
        """Check if the game is lost.
        
        Returns:
            True if there are no remaining attempts, False otherwise.
        """
        return self.remaining_attempts <= 0

    def display_progress(self) -> str:
        """Display the current progress of the game.
        
        Returns:
            A string showing guessed letters and underscores for missing ones.
        """
        return ' '.join(letter if letter in self.guessed_letters else '_' for letter in self.word)
