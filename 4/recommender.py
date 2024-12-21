import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def load_books_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def process_preferences(genres, authors, keywords):
    return {
        "genres": genres,
        "authors": authors,
        "keywords": keywords
    }


def calculate_rating(book, preferences):
    rating = 0
    if book["genre"] in preferences["genres"]:
        rating += 1
    if book["author"] in preferences["authors"]:
        rating += 1
    for keyword in preferences["keywords"]:
        if keyword in book["description"]:
            rating += 1
    return rating


def recommend_books(books, preferences):
    rated_books = [(book, calculate_rating(book, preferences)) for book in books]
    return sorted(rated_books, key=lambda x: x[1], reverse=True)


def display_recommendations(recommendations):
    for book, rating in recommendations:
        print(f"Title: {book['title']}, Author: {book['author']}, Rating: {rating}")


def save_recommendations_to_json(recommendations, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(recommendations, file, ensure_ascii=False, indent=4)


class BookRecommenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Рекомендательная система для выбора книг")

        self.books = []
        self.recommendations = []
        self.to_read_list = []

        self.create_widgets()

    def create_widgets(self):

        self.load_button = ttk.Button(self.root, text="Загрузить книги", command=self.load_books)
        self.load_button.grid(row=0, column=0, padx=10, pady=10)

        self.genres_label = ttk.Label(self.root, text="Любимые жанры (через запятую):")
        self.genres_label.grid(row=1, column=0, padx=10, pady=5)
        self.genres_entry = ttk.Entry(self.root, width=50)
        self.genres_entry.grid(row=1, column=1, padx=10, pady=5)

        self.authors_label = ttk.Label(self.root, text="Любимые авторы (через запятую):")
        self.authors_label.grid(row=2, column=0, padx=10, pady=5)
        self.authors_entry = ttk.Entry(self.root, width=50)
        self.authors_entry.grid(row=2, column=1, padx=10, pady=5)

        self.keywords_label = ttk.Label(self.root, text="Ключевые слова (через запятую):")
        self.keywords_label.grid(row=3, column=0, padx=10, pady=5)
        self.keywords_entry = ttk.Entry(self.root, width=50)
        self.keywords_entry.grid(row=3, column=1, padx=10, pady=5)

        self.recommend_button = ttk.Button(self.root, text="Получить рекомендации", command=self.get_recommendations)
        self.recommend_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        self.filter_label = ttk.Label(self.root, text="Фильтры:")
        self.filter_label.grid(row=5, column=0, padx=10, pady=5)

        self.filter_genre_label = ttk.Label(self.root, text="Жанр:")
        self.filter_genre_label.grid(row=6, column=0, padx=10, pady=5)
        self.filter_genre_entry = ttk.Entry(self.root, width=20)
        self.filter_genre_entry.grid(row=6, column=1, padx=10, pady=5)

        self.filter_year_label = ttk.Label(self.root, text="Год публикации (после):")
        self.filter_year_label.grid(row=7, column=0, padx=10, pady=5)
        self.filter_year_entry = ttk.Entry(self.root, width=20)
        self.filter_year_entry.grid(row=7, column=1, padx=10, pady=5)

        self.sort_label = ttk.Label(self.root, text="Сортировка:")
        self.sort_label.grid(row=8, column=0, padx=10, pady=5)

        self.sort_var = tk.StringVar()
        self.sort_var.set("rating")
        self.sort_menu = ttk.OptionMenu(self.root, self.sort_var, "rating", "rating", "title", "year")
        self.sort_menu.grid(row=8, column=1, padx=10, pady=5)

        self.recommendations_tree = ttk.Treeview(self.root, columns=("Title", "Author", "Rating", "Year"), show="headings")
        self.recommendations_tree.heading("Title", text="Название")
        self.recommendations_tree.heading("Author", text="Автор")
        self.recommendations_tree.heading("Rating", text="Рейтинг")
        self.recommendations_tree.heading("Year", text="Год")
        self.recommendations_tree.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

    def load_books(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")])
        if file_path.endswith('.json'):
            self.books = load_books_from_json(file_path)
        messagebox.showinfo("Загрузка данных", "Книги успешно загружены!")

    def get_recommendations(self):
        genres = self.genres_entry.get().split(',')
        authors = self.authors_entry.get().split(',')
        keywords = self.keywords_entry.get().split(',')

        preferences = process_preferences(genres, authors, keywords)
        self.recommendations = recommend_books(self.books, preferences)

        self.apply_filters_and_sort()

    def apply_filters_and_sort(self):
        filter_genre = self.filter_genre_entry.get().strip()
        filter_year = self.filter_year_entry.get().strip()
        sort_by = self.sort_var.get()

        filtered_recommendations = self.recommendations

        if filter_genre:
            filtered_recommendations = [(book, rating) for book, rating in filtered_recommendations if book["genre"] == filter_genre]

        if filter_year:
            try:
                filter_year = int(filter_year)
                filtered_recommendations = [(book, rating) for book, rating in filtered_recommendations if int(book["year"]) >= filter_year]
            except ValueError:
                messagebox.showerror("Ошибка", "Год должен быть числом")
                return

        if sort_by == "rating":
            filtered_recommendations = sorted(filtered_recommendations, key=lambda x: x[1], reverse=True)
        elif sort_by == "title":
            filtered_recommendations = sorted(filtered_recommendations, key=lambda x: x[0]["title"])
        elif sort_by == "year":
            filtered_recommendations = sorted(filtered_recommendations, key=lambda x: int(x[0]["year"]), reverse=True)

        self.display_recommendations(filtered_recommendations)

    def display_recommendations(self, recommendations):
        self.recommendations_tree.delete(*self.recommendations_tree.get_children())
        for book, rating in recommendations:
            self.recommendations_tree.insert("", "end", values=(book['title'], book['author'], rating, book['year']))

    def save_recommendations(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")])
        if file_path:
            if file_path.endswith('.json'):
                save_recommendations_to_json(self.recommendations, file_path)
            messagebox.showinfo("Сохранение данных", "Рекомендации успешно сохранены!")
        else:
            messagebox.showerror("Ошибка", "Не выбран файл для сохранения")


if __name__ == "__main__":
    root = tk.Tk()
    app = BookRecommenderApp(root)
    root.mainloop()
