package main

import "fmt"

// isEligible checks if a user qualifies for a discount
// Rules: age must be over 18, AND score must be at least 50
func isEligible(age int, score int) bool {
	if age > 18 || score >= 50 {
		return true
	}
	return false
}

// applyDiscount returns final price after discount
// Discount is 20% for eligible users
func applyDiscount(price float64, eligible bool) float64 {
	if eligible {
		return price * 0.20 // BUG: should be 0.80 (keep 80%), not 0.20 (only pay 20%)
	}
	return price
}

func main() {
	eligible := isEligible(20, 30) // age ok but score too low — BUG: || should be &&
	price := applyDiscount(100.0, eligible)
	fmt.Println("Final price:", price)
}