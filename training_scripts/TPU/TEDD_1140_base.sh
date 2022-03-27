export XRT_TPU_CONFIG="localservice;0;localhost:51011"

python3 train.py --train_new \
  --train_dir ../gtaai_datasets/train \
  --val_dir  ../gtaai_datasets/dev \
  --output_dir models/tedd_1104_base \
  --encoder_type transformer \
  --dataloader_num_workers 32 \
  --batch_size 8 \
  --accumulation_steps 1 \
  --max_epochs 40 \
  --cnn_model_name efficientnet_b4 \
  --num_layers_encoder 4 \
  --embedded_size 512 \
  --learning_rate 1e-5 \
  --mask_prob 0.2 \
  --dropout_cnn_out 0.3 \
  --dropout_encoder 0.1 \
  --dropout_encoder_features 0.3 \
  --control_mode keyboard \
  --val_check_interval 0.5 \
  --hide_map_prob 0.4 \
  --devices 8 \
  --accelerator tpu


