class Hangman {
    constructor(word) {
        this.word = word.toLowerCase();
        this.guessedLetters = new Set();
        this.remainingAttempts = 6;
        this.status = 'playing';
    }

    guess(letter) {
        if (this.status !== 'playing') {
            return;
        }

        letter = letter.toLowerCase();

        if (!this.guessedLetters.has(letter)) {
            this.guessedLetters.add(letter);

            if (!this.word.includes(letter)) {
                this.remainingAttempts--;

                if (this.remainingAttempts === 0) {
                    this.status = 'lost';
                }
            } else if (this.isWordGuessed()) {
                this.status = 'won';
            }
        }
    }

    isWordGuessed() {
        return [...this.word].every(letter => this.guessedLetters.has(letter));
    }

    get gameStatus() {
        if (this.status === 'playing') {
            return 'Keep guessing!';
        } else if (this.status === 'won') {
            return 'Congratulations! You won!';
        } else {
            return `Game over! The word was "${this.word}".`;
        }
    }

    get puzzle() {
        return [...this.word].map(letter => (this.guessedLetters.has(letter) ? letter : '_')).join(' ');
    }
}

module.exports = Hangman;
