package main

type User struct {
    name string
}

func getName(u *User) string {
    return u.name
}