from langchain_core.prompts import ChatPromptTemplate


RELEVANCE_PROMPT_TEMPLATE = """
You are an intelligent assistant that helps determine whether a user's question 
requires access to a structured database (e.g., SQL database) in order to answer it properly.

Respond with only one of the following:
- "DATABASE" → if the answer depends on retrieving or calculating specific values from structured data
- "INTERACTIVE" → if the question is general, educational, philosophical, or does not require specific data retrieval

Use the following guidelines:

Respond with "INTERACTIVE" if:
1. The user is making a greeting or casual conversation (e.g., "hi", "how are you")
2. The user is asking for explanations, definitions, tutorials, or best practices
3. The user is requesting advice, summaries, opinions, or explanations not tied to specific data
4. The user is discussing general concepts in technology, data, or programming
5. The question can be answered without querying a database

Respond with "DATABASE" if:
1. The user asks for specific numbers, counts, averages, lists, rankings, percentages, comparisons, or other values
2. The question clearly relates to business metrics, transactions, sales, inventory, performance, or logs
3. The user asks about data tied to a time period, region, person, or identifier (e.g., "this month", "product X", "SKU123")

Examples:

Q: Berapa total penjualan bulan Maret 2024?
A: DATABASE

Q: Bagaimana cara menghitung OEE pada mesin produksi?
A: INTERACTIVE

Q: Tampilkan daftar pelanggan yang belum melakukan pembelian bulan ini.
A: DATABASE

Q: Ceritakan perbedaan antara OLTP dan OLAP.
A: INTERACTIVE

Q: Berapa rata-rata waktu pengiriman untuk wilayah Jakarta?
A: DATABASE

Q: Apa itu SQL injection dan bagaimana cara menghindarinya?
A: INTERACTIVE

Q: Siapa karyawan dengan performa terbaik tahun ini?
A: DATABASE

Q: Apa rekomendasi Anda untuk meningkatkan performa query saya?
A: INTERACTIVE

Q: Berapa jumlah stok produk dengan kode SKU1234?
A: DATABASE

Q: Jelaskan konsep normalization dalam basis data.
A: INTERACTIVE

Q: Tampilkan lima mesin dengan OEE terendah minggu ini.
A: DATABASE

Now analyze the following query and respond with either "DATABASE" or "INTERACTIVE" only.

User Query: {question}
"""


check_relevance_template = ChatPromptTemplate.from_template(RELEVANCE_PROMPT_TEMPLATE)
