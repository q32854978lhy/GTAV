python3 train.py --train_new \
  --train_dir ../gtaai_datasets/train \
  --val_dir  ../gtaai_datasets/dev \
  --output_dir models/tedd_1104_large_optim \
  --encoder_type transformer \
  --dataloader_num_workers 32 \
  --batch_size 8 \
  --accumulation_steps 4 \
  --max_epochs 20 \
  --cnn_model_name efficientnet_v2_l \
  --num_layers_encoder 6 \
  --embedded_size 384 \
  --learning_rate 3e-5 \
  --mask_prob 0.2 \
  --hide_map_prob 0.0 \
  --dropout_cnn_out 0.4 \
  --dropout_encoder 0.2 \
  --dropout_encoder_features 0.5 \
  --label_smoothing 0.8 \
  --control_mode keyboard \
  --val_check_interval 0.25 \
  --precision "16"  \
  --devices 2 \
  --strategy "ddp_find_unused_parameters_false"


python3 train.py --train_new \
  --train_dir ../gtaai_datasets/train \
  --val_dir  ../gtaai_datasets/dev \
  --output_dir models/tedd_1104_large_optim_hidemap \
  --encoder_type transformer \
  --dataloader_num_workers 32 \
  --batch_size 8 \
  --accumulation_steps 4 \
  --max_epochs 20 \
  --cnn_model_name efficientnet_v2_l \
  --num_layers_encoder 6 \
  --embedded_size 384 \
  --learning_rate 3e-5 \
  --mask_prob 0.2 \
  --hide_map_prob 0.4 \
  --dropout_cnn_out 0.4 \
  --dropout_encoder 0.2 \
  --dropout_encoder_features 0.5 \
  --label_smoothing 0.8 \
  --control_mode keyboard \
  --val_check_interval 0.25 \
  --precision "16"  \
  --devices 2 \
  --strategy "ddp_find_unused_parameters_false"


