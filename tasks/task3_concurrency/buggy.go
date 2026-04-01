package main

import (
    "fmt"
    "time"
)

func main() {
    counter := 0

    for i := 0; i < 1000; i++ {
        go func() {
            counter++
        }()
    }

    time.Sleep(1 * time.Second)
    fmt.Println(counter)
}