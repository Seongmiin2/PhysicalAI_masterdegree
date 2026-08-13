from __future__ import annotations

import torch
from torch import nn


class StateEncoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, embedding_dim: int) -> None:
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.embedding = nn.Linear(hidden_dim, embedding_dim)
        self.outcome = nn.Linear(embedding_dim, 1)

    def forward(self, sequence: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        _, hidden = self.gru(sequence)
        embedding = torch.tanh(self.embedding(hidden[-1]))
        return embedding, self.outcome(embedding).squeeze(-1)
