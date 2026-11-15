class Shop:
    def __init__(self, money_amount):
        self.ma = money_amount
        self.products = []

    def buy_product(self, product):
        if self.ma >= product.price:
            self.products.append(product)
            self.ma -= product.price


    def sell_product(self, product):
        if product in self.products:
            self.products.remove(product)
            self.ma += product.price

    def __str__(self):
        return f"Shop products amount: {len(self.products)} | Shop Money amount: {self.ma}"
    

class Apple:
    def __init__(self, price):
        self.price = price
        self.name = "Apple"

    def __str__(self):
        return f'{self.name} Cost = {self.price}'
    
shop = Shop(500)

apple = Apple(25)

print(shop.buy_product(apple))
print(shop.__str__())
print(shop.sell_product(apple))
print(shop.__str__())