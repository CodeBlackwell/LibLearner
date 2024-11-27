class BasicCalculator {
    constructor() {
        this.value = 0;
    }

    add(a, b) {
        return a + b;
    }

    subtract(a, b) {
        return a - b;
    }

    multiply(a, b) {
        return a * b;
    }

    divide(a, b) {
        if (b === 0) {
            throw new Error("Cannot divide by zero");
        }
        return a / b;
    }

    sqrt(a) {
        if (a < 0) {
            throw new Error("Cannot take square root of negative number");
        }
        return Math.sqrt(a);
    }

    power(a, b) {
        return Math.pow(a, b);
    }

    handleInvalidInput(input) {
        if (typeof input !== 'number' || Number.isNaN(input)) {
            throw new Error("Invalid input");
        }
        return input;
    }
}

module.exports = BasicCalculator;
