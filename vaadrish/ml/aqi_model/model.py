import torch
import torch.nn as nn
import torch.nn.functional as F


class Attention(nn.Module):
    """Scaled dot-product attention over LSTM hidden states."""

    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.query = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.key   = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.scale = hidden_dim ** 0.5

    def forward(self, lstm_out: torch.Tensor) -> torch.Tensor:
        # lstm_out: (batch, seq_len, hidden_dim)
        Q = self.query(lstm_out)
        K = self.key(lstm_out)
        scores  = torch.bmm(Q, K.transpose(1, 2)) / self.scale  # (B, T, T)
        weights = F.softmax(scores, dim=-1)
        context = torch.bmm(weights, lstm_out)  # (B, T, H)
        return context[:, -1, :]                # take last timestep


class CNNLSTMAttention(nn.Module):
    """
    CNN-LSTM with Attention for AQI time-series prediction.

    Architecture:
        Conv1D (local feature extraction)
        -> LSTM  (temporal dependencies)
        -> Attention (focus on most relevant time steps)
        -> Fully connected regression head
    """

    def __init__(
        self,
        n_features:  int = 15,
        cnn_filters: int = 64,
        lstm_hidden: int = 128,
        lstm_layers: int = 2,
        dropout:     float = 0.3,
    ) -> None:
        super().__init__()

        #CNN block 
        self.conv1 = nn.Conv1d(n_features, cnn_filters, kernel_size=3, padding=1)
        self.bn1   = nn.BatchNorm1d(cnn_filters)
        self.conv2 = nn.Conv1d(cnn_filters, cnn_filters * 2, kernel_size=3, padding=1)
        self.bn2   = nn.BatchNorm1d(cnn_filters * 2)

        #LSTM block
        self.lstm = nn.LSTM(
            input_size=cnn_filters * 2,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0.0,
        )

        #Attention 
        self.attention = Attention(lstm_hidden)

        # Regression head
        self.dropout = nn.Dropout(dropout)
        self.fc1     = nn.Linear(lstm_hidden, 64)
        self.fc2     = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, n_features)
        # Conv1D expects (batch, channels, seq_len)
        x = x.permute(0, 2, 1)
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))

        # Back to (batch, seq_len, channels) for LSTM
        x = x.permute(0, 2, 1)
        lstm_out, _ = self.lstm(x)

        context = self.attention(lstm_out)
        x = self.dropout(F.relu(self.fc1(context)))
        return self.fc2(x).squeeze(-1)