echo "欢迎使用我的脚本！"
echo "当前目录是：$(pwd)"
cd Self-Driving-Car-in-Video-Games
echo "当前目录是：$(pwd)"
##python train.py --train_new  --train_dir dataset/train  --val_dir  dataset/dev  --output_dir runs/TEDD1104-base   --encoder_type transformer   --batch_size 16   --accumulation_steps 4   --max_epochs 12   --cnn_model_name efficientnet_b4   --num_layers_encoder 4  --mask_prob 0.2   --dropout_cnn_out 0.3   --dropout_encoder 0.1   --dropout_encoder_features 0.3   --control_mode keyboard   --dataloader_num_workers 32   --val_check_interval 0.5  --learning_rate 0.00001