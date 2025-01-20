package main

import (
    "fmt"
)

func main() {
    var num1, num2 float64

    fmt.Print("Введите первое число: ")
    fmt.Scanln(&num1)

    fmt.Print("Введите второе число: ")
    fmt.Scanln(&num2)

    sum := num1 + num2
    fmt.Printf("Сумма %.2f и %.2f равна %.2f\n", num1, num2, sum)
}