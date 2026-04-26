import numpy as np
import cv2
import matplotlib.pyplot as plt

# ----------------------------
# QUANTUM WALK (SIMULATION)
# ----------------------------
def quantum_walk(size, steps=60, seed=12345678942):
    np.random.seed(seed)

    grid = np.zeros((size, size))
    x, y = size // 2, size // 2
    grid[x, y] = 1.0

    for _ in range(steps):
        new = np.zeros_like(grid)

        for i in range(size):
            for j in range(size):
                p = grid[i, j]
                if p > 0:
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        ni, nj = (i+dx)%size, (j+dy)%size
                        new[ni, nj] += p * np.random.rand()

        grid = new / np.sum(new)

    return grid


# ----------------------------
# KEY GENERATION
# ----------------------------
def generate_key(h, w, seed=42):
    q = quantum_walk(max(h, w), seed=seed)

    key = cv2.resize(q, (w, h))
    key = (key * 1e8 % 256).astype(np.uint8)

    key = np.stack([key]*3, axis=2)
    return key


# ----------------------------
# S-BOX GENERATION (permutation)
# ----------------------------
def generate_sbox(n, seed=12345678942):
    np.random.seed(seed)
    sbox = np.arange(n)
    np.random.shuffle(sbox)
    return sbox


# ----------------------------
# APPLY S-BOX PERMUTATION
# ----------------------------
def apply_sbox(img, sbox_row, sbox_col):
    h, w, c = img.shape
    permuted = np.zeros_like(img)

    for i in range(h):
        for j in range(w):
            permuted[i, j] = img[sbox_row[i % len(sbox_row)], 
                                 sbox_col[j % len(sbox_col)]]
    return permuted


def inverse_sbox(img, sbox_row, sbox_col):
    h, w, c = img.shape
    inv = np.zeros_like(img)

    inv_row = np.argsort(sbox_row)
    inv_col = np.argsort(sbox_col)

    for i in range(h):
        for j in range(w):
            inv[i, j] = img[inv_row[i % len(inv_row)], 
                            inv_col[j % len(inv_col)]]
    return inv


# ENCRYPT
# ----------------------------
def encrypt_image(path, seed=12345678942):
    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    h, w, _ = img.shape

    key = generate_key(h, w, seed)

    # XOR step
    xored = cv2.bitwise_xor(img, key)

    # S-box permutation
    sbox_row = generate_sbox(h, seed)
    sbox_col = generate_sbox(w, seed+1)

    encrypted = apply_sbox(xored, sbox_row, sbox_col)

    return encrypted, key, sbox_row, sbox_col, img


# ----------------------------
# DECRYPT
# ----------------------------
def decrypt_image(enc, key, sbox_row, sbox_col):
    # reverse permutation
    unperm = inverse_sbox(enc, sbox_row, sbox_col)

    # XOR reverse
    dec = cv2.bitwise_xor(unperm, key)
    return dec


# ----------------------------
# VISUALIZATION HELPERS
# ----------------------------
def show_probability_distribution(seed):
    q = quantum_walk(128, steps=60, seed=seed)

    plt.figure(figsize=(5, 4))
    plt.title(f"Quantum Walk Probability (seed={seed})")
    plt.imshow(q, cmap="inferno")
    plt.colorbar()
    plt.axis("off")


def show_key_visual(key, title):
    plt.figure(figsize=(5, 4))
    plt.title(title)
    plt.imshow(key[:, :, 0], cmap="gray")
    plt.axis("off")


def show_sbox_distribution(sbox, title):
    plt.figure(figsize=(5, 3))
    plt.title(title)
    plt.plot(sbox, linewidth=1)
    plt.xlabel("Index")
    plt.ylabel("Mapped Value")


# ----------------------------
# RUN WITH VISUALIZATION
# ----------------------------
if __name__ == "__main__":
    import os

    # --- CORRECT KEY ---
    enc, key, sr, sc, original = encrypt_image("input.jpg", seed=12345678842)
    dec_correct = decrypt_image(enc, key, sr, sc)

    # --- WRONG KEY (different seed) ---
    enc2, key2, sr2, sc2, _ = encrypt_image("input.jpg", seed=12345678943)
    dec_wrong = decrypt_image(enc, key2, sr2, sc2)

    # --- KEY DIFFERENCE ---
    key_diff = cv2.absdiff(key, key2)

    # --- PROBABILITY DISTRIBUTION ---
    prob = quantum_walk(128, seed=12345678942)

    # --- SINGLE WINDOW LAYOUT ---
    fig = plt.figure(figsize=(16, 10))

    # Row 1: Images
    plt.subplot(3, 4, 1)
    plt.title("Original")
    plt.imshow(original)
    plt.axis("off")

    plt.subplot(3, 4, 2)
    plt.title("Encrypted")
    plt.imshow(enc)
    plt.axis("off")

    plt.subplot(3, 4, 3)
    plt.title("Decrypted (Correct Key)")
    plt.imshow(dec_correct)
    plt.axis("off")

    plt.subplot(3, 4, 4)
    plt.title("Decryption (Wrong Key)")
    plt.imshow(dec_wrong)
    plt.axis("off")

    # Row 2: Keys
    plt.subplot(3, 4, 5)
    plt.title("Key (seed=12345678942)")
    plt.imshow(key[:, :, 0], cmap="gray")
    plt.axis("off")

    plt.subplot(3, 4, 6)
    plt.title("Key (seed=12345678943)")
    plt.imshow(key2[:, :, 0], cmap="gray")
    plt.axis("off")

    plt.subplot(3, 4, 7)
    plt.title("Key Difference")
    plt.imshow(key_diff[:, :, 0], cmap="gray")
    plt.axis("off")

    # Probability
    plt.subplot(3, 4, 8)
    plt.title("Quantum Walk Prob.")
    plt.imshow(prob, cmap="inferno")
    plt.axis("off")

    # Row 3: S-box
    plt.subplot(3, 4, 9)
    plt.title("Row S-box")
    plt.plot(sr, linewidth=1)

    plt.subplot(3, 4, 10)
    plt.title("Column S-box")
    plt.plot(sc, linewidth=1)

    # Empty slots (optional text info)
    plt.subplot(3, 4, 11)
    plt.title("Info")
    plt.text(0.1, 0.5, "XOR + S-box Encryption\nQuantum Walk Key\nSeed Sensitive", fontsize=10)
    plt.axis("off")

    plt.subplot(3, 4, 12)
    plt.axis("off")

    plt.tight_layout()

    # Save outputs
    os.makedirs("output", exist_ok=True)
    plt.savefig("output/full_dashboard.png", dpi=150)

    print("Saved output/full_dashboard.png")

    plt.show()