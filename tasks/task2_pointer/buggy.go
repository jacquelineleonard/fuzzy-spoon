package main

import "fmt"

type User struct {
	ID    int
	Name  string
	Email string
}

type Order struct {
	ID     int
	UserID int
	Amount float64
}

// findUser looks up a user by ID
// Returns nil if not found — but caller doesn't always check
func findUser(id int, users []User) *User {
	for _, u := range users {
		if u.ID == id {
			return &u
		}
	}
	return nil // BUG SOURCE: returns nil silently
}

// getOrderOwnerEmail returns the email of whoever placed an order
func getOrderOwnerEmail(order Order, users []User) string {
	user := findUser(order.UserID, users)
	// BUG: no nil check here — if UserID doesn't match any user, this panics
	return user.Email
}

// processOrders sends confirmation emails for all orders
func processOrders(orders []Order, users []User) {
	for _, order := range orders {
		email := getOrderOwnerEmail(order, users)
		fmt.Printf("Sending confirmation to %s for order %d\n", email, order.ID)
	}
}

func main() {
	users := []User{
		{ID: 1, Name: "Alice", Email: "alice@example.com"},
		{ID: 2, Name: "Bob", Email: "bob@example.com"},
	}

	orders := []Order{
		{ID: 101, UserID: 1, Amount: 50.0},
		{ID: 102, UserID: 99, Amount: 75.0}, // UserID 99 doesn't exist — will panic
		{ID: 103, UserID: 2, Amount: 30.0},
	}

	processOrders(orders, users)
}