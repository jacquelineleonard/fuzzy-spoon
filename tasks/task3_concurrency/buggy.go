package main

import (
	"fmt"
	"sort"
)

type Product struct {
	ID    int
	Name  string
	Price float64
	Stock int
}

// getPage returns a page of products
// IMPORTANT: page param is documented as 1-indexed (page 1 = first page)
// but internally calculated as 0-indexed — this creates a hidden off-by-one
func getPage(products []Product, page int, pageSize int) []Product {
	// BUG 1: treats page as 0-indexed but callers use 1-indexed
	start := page * pageSize
	end := start + pageSize

	// BUG 2: no bounds check — panics if start >= len(products)
	// BUG 3: end is not clamped — panics on last partial page
	return products[start:end]
}

// filterInStock removes out-of-stock items
// BUG 4: modifies slice in-place while iterating — skips every other element
func filterInStock(products []Product) []Product {
	for i := 0; i < len(products); i++ {
		if products[i].Stock == 0 {
			products = append(products[:i], products[i+1:]...)
			// missing: i-- after removal, so next element is skipped
		}
	}
	return products
}

// getTopProducts returns the top N products by price, paginated
// combines both buggy functions — compound failure
func getTopProducts(products []Product, page int, pageSize int) []Product {
	inStock := filterInStock(products)

	sort.Slice(inStock, func(i, j int) bool {
		return inStock[i].Price > inStock[j].Price
	})

	return getPage(inStock, page, pageSize)
}

func main() {
	products := []Product{
		{ID: 1, Name: "Laptop", Price: 999.99, Stock: 5},
		{ID: 2, Name: "Mouse", Price: 29.99, Stock: 0},
		{ID: 3, Name: "Keyboard", Price: 79.99, Stock: 3},
		{ID: 4, Name: "Monitor", Price: 399.99, Stock: 0},
		{ID: 5, Name: "Headphones", Price: 149.99, Stock: 2},
		{ID: 6, Name: "Webcam", Price: 89.99, Stock: 0},
	}

	// Caller uses page=1 meaning "first page" — but getPage treats it as page index 1 (second page)
	result := getTopProducts(products, 1, 2)
	fmt.Println("Top products page 1:")
	for _, p := range result {
		fmt.Printf("  %s $%.2f\n", p.Name, p.Price)
	}
}