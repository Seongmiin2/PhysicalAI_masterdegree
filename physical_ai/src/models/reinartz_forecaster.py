from __future__ import annotations

import torch
from torch import nn


class GRUForecaster(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, layers: int, output_dim: int = 41) -> None:
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, num_layers=layers, batch_first=True)
        self.output = nn.Linear(hidden_dim, output_dim)

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        _, hidden = self.gru(sequence)
        return self.output(hidden[-1])
